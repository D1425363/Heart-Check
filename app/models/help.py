import datetime
from app.models.db import get_db_connection

# 分類對應中文名稱與圖示
CATEGORY_META = {
    'notes':    {'label': '找筆記',  'icon': '📓', 'color': '#6366f1'},
    'team':     {'label': '找組員',  'icon': '🤝', 'color': '#8b5cf6'},
    'lost':     {'label': '找失物',  'icon': '🔍', 'color': '#ec4899'},
    'textbook': {'label': '找課本',  'icon': '📚', 'color': '#f59e0b'},
    'course':   {'label': '問課程',  'icon': '🎓', 'color': '#10b981'},
}

VALID_CATEGORIES = list(CATEGORY_META.keys())


class HelpRequest:
    def __init__(self, id, user_id, category, title, description, status, created_at, updated_at,
                 author_name=None, author_department=None):
        self.id = id
        self.user_id = user_id
        self.category = category
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.author_name = author_name
        self.author_department = author_department

        # Attach category metadata
        meta = CATEGORY_META.get(category, {'label': category, 'icon': '❓', 'color': '#888'})
        self.category_label = meta['label']
        self.category_icon = meta['icon']
        self.category_color = meta['color']

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        author_name = row['author_name'] if 'author_name' in row.keys() else None
        author_department = row['author_department'] if 'author_department' in row.keys() else None
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            category=row['category'],
            title=row['title'],
            description=row['description'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            author_name=author_name,
            author_department=author_department,
        )

    @classmethod
    def create(cls, user_id, category, title, description):
        """新增一筆求助需求。"""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"無效的分類：{category}")
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO help_requests (user_id, category, title, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'open', ?, ?);
                """,
                (user_id, category, title, description, now, now)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return cls.get_by_id(new_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, request_id):
        conn = get_db_connection()
        row = conn.execute(
            """
            SELECT hr.*, u.name AS author_name, u.department AS author_department
            FROM help_requests hr
            JOIN users u ON hr.user_id = u.id
            WHERE hr.id = ?;
            """,
            (request_id,)
        ).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls, category=None, status=None):
        """取得所有求助（可依分類 & 狀態篩選）。"""
        conn = get_db_connection()
        query = """
            SELECT hr.*, u.name AS author_name, u.department AS author_department
            FROM help_requests hr
            JOIN users u ON hr.user_id = u.id
            WHERE 1=1
        """
        params = []
        if category:
            query += " AND hr.category = ?"
            params.append(category)
        if status:
            query += " AND hr.status = ?"
            params.append(status)
        query += " ORDER BY hr.created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user_id(cls, user_id):
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT hr.*, u.name AS author_name, u.department AS author_department
            FROM help_requests hr
            JOIN users u ON hr.user_id = u.id
            WHERE hr.user_id = ?
            ORDER BY hr.created_at DESC;
            """,
            (user_id,)
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    def mark_resolved(self):
        """標記此求助為已解決。"""
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE help_requests SET status = 'resolved', updated_at = ? WHERE id = ?;",
                (now, self.id)
            )
            conn.commit()
            self.status = 'resolved'
            self.updated_at = now
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self):
        """刪除此筆求助。"""
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM help_requests WHERE id = ?;", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
