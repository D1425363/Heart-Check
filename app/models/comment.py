import datetime
from app.models.db import get_db_connection

class Comment:
    def __init__(self, id, item_id, user_id, content, created_at, user_name=None):
        self.id = id
        self.item_id = item_id
        self.user_id = user_id
        self.content = content
        self.created_at = created_at
        
        # Optional joined fields
        self.user_name = user_name

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        user_name = row['user_name'] if 'user_name' in row.keys() else None
        
        return cls(
            id=row['id'],
            item_id=row['item_id'],
            user_id=row['user_id'],
            content=row['content'],
            created_at=row['created_at'],
            user_name=user_name
        )

    @classmethod
    def create(cls, item_id, user_id, content):
        """
        Creates a new comment on a lost & found item.
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty.")
            
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO item_comments (item_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (item_id, user_id, content.strip(), now)
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
    def get_by_id(cls, comment_id):
        """
        Retrieves a comment by ID.
        """
        conn = get_db_connection()
        row = conn.execute(
            """
            SELECT c.*, u.name AS user_name
            FROM item_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?;
            """,
            (comment_id,)
        ).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_by_item_id(cls, item_id):
        """
        Retrieves all comments for a specific item, sorted by time (oldest first).
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT c.*, u.name AS user_name
            FROM item_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.item_id = ?
            ORDER BY c.created_at ASC;
            """,
            (item_id,)
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def delete(cls, comment_id):
        """
        Deletes a comment.
        """
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM item_comments WHERE id = ?;", (comment_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
