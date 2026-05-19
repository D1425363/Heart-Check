import datetime
from app.models.db import get_db_connection

class Item:
    def __init__(self, id, title, description, image_url, location, item_type, status, user_id, contact_info, created_at, updated_at, user_name=None):
        self.id = id
        self.title = title
        self.description = description
        self.image_url = image_url
        self.location = location
        self.item_type = item_type  # 'lost' or 'found'
        self.status = status        # 'unclaimed' or 'claimed'
        self.user_id = user_id
        self.contact_info = contact_info
        self.created_at = created_at
        self.updated_at = updated_at
        
        # Optional joined fields
        self.user_name = user_name

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        user_name = row['user_name'] if 'user_name' in row.keys() else None
        
        return cls(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            image_url=row['image_url'],
            location=row['location'],
            item_type=row['item_type'],
            status=row['status'],
            user_id=row['user_id'],
            contact_info=row['contact_info'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            user_name=user_name
        )

    @classmethod
    def create(cls, title, description, location, item_type, status='unclaimed', user_id=None, image_url=None, contact_info=None):
        """
        Creates a new lost & found item.
        """
        if item_type not in ('lost', 'found'):
            raise ValueError("item_type must be either 'lost' or 'found'.")
        if status not in ('unclaimed', 'claimed'):
            raise ValueError("status must be either 'unclaimed' or 'claimed'.")
        if not user_id:
            raise ValueError("user_id is required.")

        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO items (title, description, image_url, location, item_type, status, user_id, contact_info, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (title, description, image_url, location, item_type, status, user_id, contact_info, now, now)
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
    def get_by_id(cls, item_id):
        """
        Retrieves a single item by its ID.
        """
        conn = get_db_connection()
        row = conn.execute(
            """
            SELECT i.*, u.name AS user_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.id = ?;
            """,
            (item_id,)
        ).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls):
        """
        Retrieves all items sorted by creation time (newest first).
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT i.*, u.name AS user_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC;
            """
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_type(cls, item_type):
        """
        Retrieves items filtered by type ('lost' or 'found').
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT i.*, u.name AS user_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.item_type = ?
            ORDER BY i.created_at DESC;
            """,
            (item_type,)
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Retrieves items posted by a specific user.
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT i.*, u.name AS user_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.user_id = ?
            ORDER BY i.created_at DESC;
            """,
            (user_id,)
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    def update(self):
        """
        Updates the item information in the database.
        """
        if self.item_type not in ('lost', 'found'):
            raise ValueError("item_type must be either 'lost' or 'found'.")
        if self.status not in ('unclaimed', 'claimed'):
            raise ValueError("status must be either 'unclaimed' or 'claimed'.")

        self.updated_at = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE items
                SET title = ?, description = ?, image_url = ?, location = ?,
                    item_type = ?, status = ?, user_id = ?, contact_info = ?, updated_at = ?
                WHERE id = ?;
                """,
                (self.title, self.description, self.image_url, self.location,
                 self.item_type, self.status, self.user_id, self.contact_info, self.updated_at, self.id)
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
        Deletes the item from the database.
        """
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM items WHERE id = ?;", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
