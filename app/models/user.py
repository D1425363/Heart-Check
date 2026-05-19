import datetime
import secrets
from app.models.db import get_db_connection

class User:
    def __init__(self, id, username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.name = name
        self.student_id = student_id
        self.department = department
        self.heart_balance = heart_balance
        self.popularity = popularity
        self.qr_code_token = qr_code_token
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            name=row['name'],
            student_id=row['student_id'],
            department=row['department'],
            heart_balance=row['heart_balance'],
            popularity=row['popularity'],
            qr_code_token=row['qr_code_token'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    @classmethod
    def create(cls, username, password_hash, name, student_id, department=None, heart_balance=100, popularity=0, qr_code_token=None):
        """
        Creates a new user in the database.
        """
        now = datetime.datetime.now().isoformat()
        if not qr_code_token:
            qr_code_token = secrets.token_hex(16)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, now, now)
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
    def get_by_id(cls, user_id):
        """
        Retrieves a user by their ID.
        """
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_by_username(cls, username):
        """
        Retrieves a user by their username.
        """
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_by_qr_code_token(cls, qr_code_token):
        """
        Retrieves a user by their unique QR code token.
        """
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE qr_code_token = ?;", (qr_code_token,)).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls):
        """
        Retrieves all users.
        """
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC;").fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_top_by_popularity(cls, limit=10):
        """
        Retrieves top users sorted by popularity (leaderboard).
        """
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM users ORDER BY popularity DESC, name ASC LIMIT ?;", (limit,)).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    def update(self):
        """
        Updates the current user's profile and dynamic attributes in the database.
        """
        self.updated_at = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE users 
                SET username = ?, password_hash = ?, name = ?, student_id = ?, department = ?, 
                    heart_balance = ?, popularity = ?, qr_code_token = ?, updated_at = ?
                WHERE id = ?;
                """,
                (self.username, self.password_hash, self.name, self.student_id, self.department,
                 self.heart_balance, self.popularity, self.qr_code_token, self.updated_at, self.id)
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
        Deletes the user from the database.
        """
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM users WHERE id = ?;", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class HeartTransaction:
    def __init__(self, id, sender_id, receiver_id, heart_amount, thank_you_message, created_at, sender_name=None, receiver_name=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.heart_amount = heart_amount
        self.thank_you_message = thank_you_message
        self.created_at = created_at
        
        # Optional joined fields for convenience
        self.sender_name = sender_name
        self.receiver_name = receiver_name

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        # Handle optional joined columns if they exist in the row
        sender_name = row['sender_name'] if 'sender_name' in row.keys() else None
        receiver_name = row['receiver_name'] if 'receiver_name' in row.keys() else None
        
        return cls(
            id=row['id'],
            sender_id=row['sender_id'],
            receiver_id=row['receiver_id'],
            heart_amount=row['heart_amount'],
            thank_you_message=row['thank_you_message'],
            created_at=row['created_at'],
            sender_name=sender_name,
            receiver_name=receiver_name
        )

    @classmethod
    def create(cls, sender_id, receiver_id, heart_amount, thank_you_message=None):
        """
        Records a transaction without transferring balance. 
        Use transfer_hearts() for transferring hearts and recording transaction atomically.
        """
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO heart_transactions (sender_id, receiver_id, heart_amount, thank_you_message, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (sender_id, receiver_id, heart_amount, thank_you_message, now)
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
    def transfer_hearts(cls, sender_id, receiver_id, amount, message=None):
        """
        Atomically transfers hearts from sender to receiver, increasing receiver popularity,
        and logs the transaction.
        """
        if sender_id == receiver_id:
            raise ValueError("Cannot transfer heart values to yourself.")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 1. Fetch sender and check balance
            sender_row = cursor.execute("SELECT heart_balance FROM users WHERE id = ?;", (sender_id,)).fetchone()
            if not sender_row:
                raise ValueError("Sender user not found.")
            
            if sender_row['heart_balance'] < amount:
                raise ValueError("Insufficient heart balance.")

            # 2. Verify receiver exists
            receiver_exists = cursor.execute("SELECT 1 FROM users WHERE id = ?;", (receiver_id,)).fetchone()
            if not receiver_exists:
                raise ValueError("Receiver user not found.")

            # 3. Deduct from sender
            cursor.execute(
                "UPDATE users SET heart_balance = heart_balance - ?, updated_at = ? WHERE id = ?;",
                (amount, now, sender_id)
            )

            # 4. Add to receiver popularity
            cursor.execute(
                "UPDATE users SET popularity = popularity + ?, updated_at = ? WHERE id = ?;",
                (amount, now, receiver_id)
            )

            # 5. Insert transaction log
            cursor.execute(
                """
                INSERT INTO heart_transactions (sender_id, receiver_id, heart_amount, thank_you_message, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (sender_id, receiver_id, amount, message, now)
            )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, transaction_id):
        """
        Retrieves a single transaction by ID.
        """
        conn = get_db_connection()
        row = conn.execute(
            """
            SELECT t.*, u1.name AS sender_name, u2.name AS receiver_name
            FROM heart_transactions t
            JOIN users u1 ON t.sender_id = u1.id
            JOIN users u2 ON t.receiver_id = u2.id
            WHERE t.id = ?;
            """,
            (transaction_id,)
        ).fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls):
        """
        Retrieves all transactions.
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT t.*, u1.name AS sender_name, u2.name AS receiver_name
            FROM heart_transactions t
            JOIN users u1 ON t.sender_id = u1.id
            JOIN users u2 ON t.receiver_id = u2.id
            ORDER BY t.created_at DESC;
            """
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Retrieves all transactions where user_id is sender or receiver.
        """
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT t.*, u1.name AS sender_name, u2.name AS receiver_name
            FROM heart_transactions t
            JOIN users u1 ON t.sender_id = u1.id
            JOIN users u2 ON t.receiver_id = u2.id
            WHERE t.sender_id = ? OR t.receiver_id = ?
            ORDER BY t.created_at DESC;
            """,
            (user_id, user_id)
        ).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    def delete(self):
        """
        Deletes a transaction.
        """
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM heart_transactions WHERE id = ?;", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
