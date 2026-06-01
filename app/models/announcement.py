import datetime
from app.models.db import get_db_connection

def get_local_db_connection():
    """
    建立並回傳 SQLite 資料庫連線，啟用外鍵約束，並設定 Row Factory。
    
    Returns:
        sqlite3.Connection: 資料庫連線物件。
    """
    try:
        return get_db_connection()
    except Exception as e:
        print(f"Error establishing database connection in Announcement model: {e}")
        raise e

class Announcement:
    def __init__(self, id, title, content, category, author_id, created_at, updated_at, author_name=None):
        self.id = id
        self.title = title
        self.content = content
        self.category = category  # 'dorm' or 'campus'
        self.author_id = author_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.author_name = author_name

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        author_name = row['author_name'] if 'author_name' in row.keys() else None
        
        return cls(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            category=row['category'],
            author_id=row['author_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            author_name=author_name
        )

    @classmethod
    def create(cls, data=None, **kwargs):
        """
        新增一筆公告記錄。
        
        參數:
            data (dict, optional): 包含公告欄位的字典。
            **kwargs: 可選的關鍵字引數。
        
        傳回值:
            Announcement: 新增的公告物件。
        """
        try:
            if isinstance(data, dict):
                title = data.get('title')
                content = data.get('content')
                category = data.get('category')
                author_id = data.get('author_id')
            else:
                title = data if data is not None else kwargs.get('title')
                content = kwargs.get('content')
                category = kwargs.get('category')
                author_id = kwargs.get('author_id')

            if category not in ('dorm', 'campus'):
                raise ValueError("category must be either 'dorm' or 'campus'.")
            if not author_id:
                raise ValueError("author_id is required.")

            now = datetime.datetime.now().isoformat()
            conn = get_local_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO announcements (title, content, category, author_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (title, content, category, author_id, now, now)
                )
                conn.commit()
                new_id = cursor.lastrowid
                return cls.get_by_id(new_id)
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.create: {e}")
            raise e

    @classmethod
    def get_by_id(cls, announcement_id):
        """
        取得單筆公告記錄（依 ID）。
        
        參數:
            announcement_id (int): 公告 ID。
            
        傳回值:
            Announcement: 公告物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
                row = conn.execute(
                    """
                    SELECT a.*, u.name AS author_name
                    FROM announcements a
                    JOIN users u ON a.author_id = u.id
                    WHERE a.id = ?;
                    """,
                    (announcement_id,)
                ).fetchone()
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.get_by_id: {e}")
            raise e

    @classmethod
    def get_all(cls):
        """
        取得所有公告記錄（依建立時間降冪排序）。
        
        傳回值:
            list: 包含所有 Announcement 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT a.*, u.name AS author_name
                    FROM announcements a
                    JOIN users u ON a.author_id = u.id
                    ORDER BY a.created_at DESC;
                    """
                ).fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.get_all: {e}")
            raise e

    @classmethod
    def get_by_category(cls, category):
        """
        依公告分類取得公告記錄（dorm/campus）。
        
        參數:
            category (str): 'dorm' 或 'campus'。
            
        傳回值:
            list: 包含 Announcement 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT a.*, u.name AS author_name
                    FROM announcements a
                    JOIN users u ON a.author_id = u.id
                    WHERE a.category = ?
                    ORDER BY a.created_at DESC;
                    """,
                    (category,)
                ).fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.get_by_category: {e}")
            raise e

    @classmethod
    def update(cls, id_or_self, data=None):
        """
        更新公告記錄。支援物件導向式更新與類別層級更新。
        
        參數:
            id_or_self (int/Announcement): 公告 ID 或 Announcement 物件。
            data (dict, optional): 欲更新的欄位與值字典。
            
        傳回值:
            bool: 更新成功傳回 True，否則傳回 False。
        """
        try:
            now = datetime.datetime.now().isoformat()
            conn = get_local_db_connection()
            try:
                if isinstance(id_or_self, cls):
                    # 物件導向式更新
                    self = id_or_self
                    if self.category not in ('dorm', 'campus'):
                        raise ValueError("category must be either 'dorm' or 'campus'.")
                    self.updated_at = now
                    conn.execute(
                        """
                        UPDATE announcements
                        SET title = ?, content = ?, category = ?, author_id = ?, updated_at = ?
                        WHERE id = ?;
                        """,
                        (self.title, self.content, self.category, self.author_id, self.updated_at, self.id)
                    )
                    conn.commit()
                    return True
                else:
                    # 類別層級更新
                    announcement_id = id_or_self
                    if not data:
                        return False
                    
                    if 'category' in data and data['category'] not in ('dorm', 'campus'):
                        raise ValueError("category must be either 'dorm' or 'campus'.")

                    fields = []
                    params = []
                    for key, val in data.items():
                        if key in ('title', 'content', 'category', 'author_id'):
                            fields.append(f"{key} = ?")
                            params.append(val)
                    
                    if not fields:
                        return False
                    
                    fields.append("updated_at = ?")
                    params.append(now)
                    params.append(announcement_id)
                    
                    sql = f"UPDATE announcements SET {', '.join(fields)} WHERE id = ?;"
                    conn.execute(sql, tuple(params))
                    conn.commit()
                    return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.update: {e}")
            raise e

    @classmethod
    def delete(cls, id_or_self):
        """
        刪除公告記錄。支援物件導向式與類別層級。
        
        參數:
            id_or_self (int/Announcement): 公告 ID 或 Announcement 物件。
            
        傳回值:
            bool: 刪除成功傳回 True，否則傳回 False。
        """
        try:
            announcement_id = id_or_self.id if isinstance(id_or_self, cls) else id_or_self
            conn = get_local_db_connection()
            try:
                conn.execute("DELETE FROM announcements WHERE id = ?;", (announcement_id,))
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Announcement.delete: {e}")
            raise e
