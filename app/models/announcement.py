import datetime
from app.models.db import get_db_connection

class Announcement:
    def __init__(self, id, title, content, category, author_id, created_at, updated_at, author_name=None):
        self.id = id
        self.title = title
        self.content = content
        self.category = category  # 'dorm' or 'campus'
        self.author_id = author_id
        self.created_at = created_at
        self.updated_at = updated_at
        
        # Optional joined fields
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
    def create(cls, title, content, category, author_id):
        """
        Creates a new announcement.
        """
        if category not in ('dorm', 'campus'):
            raise ValueError("category must be either 'dorm' or 'campus'.")
        if not author_id:
            raise ValueError("author_id is required.")

        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
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

    @classmethod
    def get_by_id(cls, announcement_id):
        """
        Retrieves a single announcement by its ID.
        """
        conn = get_db_connection()
        row = conn.execute(
            """
            SELECT a.*, u.name AS author_name
            FROM announcements a
            JOIN users u ON a.author_id = u.id
            WHERE a.id = ?;
            """,
            (announcement_id,)
        ).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls):
        """
        Retrieves all announcements sorted by creation time (newest first).
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT a.*, u.name AS author_name
            FROM announcements a
            JOIN users u ON a.author_id = u.id
            ORDER BY a.created_at DESC;
            """
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_category(cls, category):
        """
        Retrieves announcements filtered by category ('dorm' or 'campus').
        """
        conn = get_db_connection()
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
        conn.close()
        return [cls.from_row(row) for row in rows]

    def update(self):
        """
        Updates the announcement in the database.
        """
        if self.category not in ('dorm', 'campus'):
            raise ValueError("category must be either 'dorm' or 'campus'.")

        self.updated_at = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        try:
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
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self):
        """
        Deletes the announcement from the database.
        """
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM announcements WHERE id = ?;", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
