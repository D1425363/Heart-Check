import datetime
import secrets
from app.models.db import get_db_connection

def _get_period_start(period):
    now = datetime.datetime.now()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif period == "week":
        # Monday is 0, Sunday is 6
        start_of_week = now - datetime.timedelta(days=now.weekday())
        return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    return None

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

    @classmethod
    def get_top_by_period(cls, period="total", limit=10):
        """
        Retrieves top users sorted by popularity in a given period (today, week, month, total).
        """
        if period == "total":
            users = cls.get_top_by_popularity(limit=limit)
            for u in users:
                u.period_popularity = u.popularity
            return users
            
        start_date = _get_period_start(period)
        if not start_date:
            return []
            
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT u.*, COALESCE(SUM(t.heart_amount), 0) AS period_popularity
            FROM users u
            LEFT JOIN heart_transactions t ON u.id = t.receiver_id AND t.created_at >= ?
            GROUP BY u.id
            ORDER BY period_popularity DESC, u.name ASC
            LIMIT ?;
            """,
            (start_date, limit)
        ).fetchall()
        conn.close()
        
        users = []
        for row in rows:
            u = cls.from_row(row)
            if u:
                u.period_popularity = row['period_popularity']
                users.append(u)
        return users

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


# Badge metadata for the 7 available badges
BADGE_METADATA = {
    'helper': {'name': '熱心人士', 'desc': '幫助 5 位不同同學（即收到來自 5 位不同同學的愛心值轉移）', 'icon': '🤝'},
    'poster': {'name': '校園情報員', 'desc': '發布 10 篇資訊（即累計發布 10 篇失物招領公告）', 'icon': '📢'},
    'heart_helper': {'name': '校園暖心小幫手', 'desc': '累計獲得 10 顆愛心（即累積人氣值達到 10 或以上）', 'icon': '💖'},
    'ambassador': {'name': '愛心大使', 'desc': '累計送出 50 顆愛心給其他同學', 'icon': '🌟'},
    'expert': {'name': '尋物達人', 'desc': '發布的失物招領公告中，有 3 篇成功標記為「已尋回/已認領」', 'icon': '🔍'},
    'grateful': {'name': '感恩的心', 'desc': '送出愛心時，累計填寫了 5 次感謝留言', 'icon': '✉️'},
    'rookie': {'name': '初試身手', 'desc': '完成第一次愛心傳遞（不論是送出還是收到）', 'icon': '🌱'}
}


class Badge:
    def __init__(self, id, user_id, badge_type, is_pinned, created_at):
        self.id = id
        self.user_id = user_id
        self.badge_type = badge_type
        self.is_pinned = is_pinned
        self.created_at = created_at
        
        # Meta info
        meta = BADGE_METADATA.get(badge_type, {'name': '未知徽章', 'desc': '', 'icon': '❓'})
        self.name = meta['name']
        self.desc = meta['desc']
        self.icon = meta['icon']

    @classmethod
    def get_by_user_id(cls, user_id):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM user_badges WHERE user_id = ? ORDER BY created_at ASC;", (user_id,)).fetchall()
        conn.close()
        return [cls(row['id'], row['user_id'], row['badge_type'], row['is_pinned'], row['created_at']) for row in rows]

    @classmethod
    def get_pinned_by_user_id(cls, user_id):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM user_badges WHERE user_id = ? AND is_pinned = 1 ORDER BY created_at ASC;", (user_id,)).fetchall()
        conn.close()
        return [cls(row['id'], row['user_id'], row['badge_type'], row['is_pinned'], row['created_at']) for row in rows]

    @classmethod
    def pin_badges(cls, user_id, badge_types):
        if len(badge_types) > 3:
            badge_types = badge_types[:3]
        
        conn = get_db_connection()
        try:
            # First reset all pins for this user
            conn.execute("UPDATE user_badges SET is_pinned = 0 WHERE user_id = ?;", (user_id,))
            if badge_types:
                # Placeholders for IN clause
                placeholders = ",".join("?" for _ in badge_types)
                conn.execute(
                    f"UPDATE user_badges SET is_pinned = 1 WHERE user_id = ? AND badge_type IN ({placeholders});",
                    [user_id] + list(badge_types)
                )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def check_and_award(cls, user_id):
        """
        Checks requirements for all 7 badges and awards any that are earned but not yet recorded.
        Returns a list of newly awarded Badge objects.
        """
        conn = get_db_connection()
        new_awards = []
        try:
            # Fetch existing badge types
            existing_rows = conn.execute("SELECT badge_type FROM user_badges WHERE user_id = ?;", (user_id,)).fetchall()
            existing_badges = {row['badge_type'] for row in existing_rows}

            # Helper functions to query data
            helped_count = conn.execute(
                "SELECT COUNT(DISTINCT sender_id) FROM heart_transactions WHERE receiver_id = ?;",
                (user_id,)
            ).fetchone()[0] or 0

            posted_count = conn.execute(
                "SELECT COUNT(*) FROM items WHERE user_id = ?;",
                (user_id,)
            ).fetchone()[0] or 0

            user_row = conn.execute("SELECT popularity FROM users WHERE id = ?;", (user_id,)).fetchone()
            popularity = user_row['popularity'] if user_row else 0

            hearts_sent = conn.execute(
                "SELECT SUM(heart_amount) FROM heart_transactions WHERE sender_id = ?;",
                (user_id,)
            ).fetchone()[0] or 0

            resolved_count = conn.execute(
                "SELECT COUNT(*) FROM items WHERE user_id = ? AND status = 'claimed';",
                (user_id,)
            ).fetchone()[0] or 0

            grateful_count = conn.execute(
                """
                SELECT COUNT(*) FROM heart_transactions 
                WHERE sender_id = ? AND thank_you_message IS NOT NULL AND thank_you_message != '';
                """,
                (user_id,)
            ).fetchone()[0] or 0

            total_trans = conn.execute(
                "SELECT COUNT(*) FROM heart_transactions WHERE sender_id = ? OR receiver_id = ?;",
                (user_id, user_id)
            ).fetchone()[0] or 0

            # Map check logic
            checks = {
                'helper': helped_count >= 5,
                'poster': posted_count >= 10,
                'heart_helper': popularity >= 10,
                'ambassador': hearts_sent >= 50,
                'expert': resolved_count >= 3,
                'grateful': grateful_count >= 5,
                'rookie': total_trans >= 1
            }

            now = datetime.datetime.now().isoformat()
            for badge_type, earned in checks.items():
                if earned and badge_type not in existing_badges:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO user_badges (user_id, badge_type, is_pinned, created_at) VALUES (?, ?, 0, ?);",
                        (user_id, badge_type, now)
                    )
                    new_id = cursor.lastrowid
                    new_awards.append(cls(new_id, user_id, badge_type, 0, now))

            if new_awards:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return new_awards

