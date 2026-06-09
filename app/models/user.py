import datetime
import secrets
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
        print(f"Error establishing database connection: {e}")
        raise e

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
    def create(cls, data=None, **kwargs):
        """
        新增一筆使用者記錄。
        
        參數:
            data (dict, optional): 包含使用者欄位的字典。
            **kwargs: 可選的關鍵字引數。
        
        傳回值:
            User: 新增的使用者物件。
        """
        try:
            if isinstance(data, dict):
                username = data.get('username')
                password_hash = data.get('password_hash')
                name = data.get('name')
                student_id = data.get('student_id')
                department = data.get('department')
                heart_balance = data.get('heart_balance', 100)
                popularity = data.get('popularity', 0)
                qr_code_token = data.get('qr_code_token')
            else:
                username = data if data is not None else kwargs.get('username')
                password_hash = kwargs.get('password_hash')
                name = kwargs.get('name')
                student_id = kwargs.get('student_id')
                department = kwargs.get('department')
                heart_balance = kwargs.get('heart_balance', 100)
                popularity = kwargs.get('popularity', 0)
                qr_code_token = kwargs.get('qr_code_token')

            now = datetime.datetime.now().isoformat()
            if not qr_code_token:
                qr_code_token = secrets.token_hex(16)

            conn = get_local_db_connection()
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
        except Exception as e:
            print(f"Error in User.create: {e}")
            raise e

    @classmethod
    def get_by_id(cls, user_id):
        """
        取得單筆使用者記錄（依 ID）。
        
        參數:
            user_id (int): 使用者 ID。
            
        傳回值:
            User: 使用者物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
                row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_by_id: {e}")
            raise e

    @classmethod
    def get_by_username(cls, username):
        """
        取得單筆使用者記錄（依使用者帳號）。
        
        參數:
            username (str): 使用者帳號。
            
        傳回值:
            User: 使用者物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
                row = conn.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone()
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_by_username: {e}")
            raise e

    @classmethod
    def get_by_qr_code_token(cls, qr_code_token):
        """
        取得單筆使用者記錄（依 QR Code Token）。
        
        參數:
            qr_code_token (str): QR Code 憑證。
            
        傳回值:
            User: 使用者物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
                row = conn.execute("SELECT * FROM users WHERE qr_code_token = ?;", (qr_code_token,)).fetchone()
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_by_qr_code_token: {e}")
            raise e

    @classmethod
    def get_all(cls):
        """
        取得所有使用者記錄。
        
        傳回值:
            list: 包含所有 User 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute("SELECT * FROM users ORDER BY id ASC;").fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_all: {e}")
            raise e

    @classmethod
    def get_top_by_popularity(cls, limit=10):
        """
        取得人氣排行榜前幾名使用者。
        
        參數:
            limit (int): 取得數量限制。
            
        傳回值:
            list: 包含 User 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute("SELECT * FROM users ORDER BY popularity DESC, name ASC LIMIT ?;", (limit,)).fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_top_by_popularity: {e}")
            raise e

    @classmethod
    def update(cls, id_or_self, data=None):
        """
        更新使用者記錄。支援物件導向式更新與類別層級更新。
        
        參數:
            id_or_self (int/User): 使用者 ID 或 User 物件。
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
                    self.updated_at = now
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
                else:
                    # 類別層級更新
                    user_id = id_or_self
                    if not data:
                        return False
                    
                    # 動態生成 SQL 以支援局部更新
                    fields = []
                    params = []
                    for key, val in data.items():
                        if key in ('username', 'password_hash', 'name', 'student_id', 'department', 'heart_balance', 'popularity', 'qr_code_token'):
                            fields.append(f"{key} = ?")
                            params.append(val)
                    
                    if not fields:
                        return False
                    
                    fields.append("updated_at = ?")
                    params.append(now)
                    params.append(user_id)
                    
                    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?;"
                    conn.execute(sql, tuple(params))
                    conn.commit()
                    return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.update: {e}")
            raise e

    @classmethod
    def delete(cls, id_or_self):
        """
        刪除使用者記錄。支援物件導向式刪除與類別層級刪除。
        
        參數:
            id_or_self (int/User): 使用者 ID 或 User 物件。
            
        傳回值:
            bool: 刪除成功傳回 True，否則傳回 False。
        """
        try:
            user_id = id_or_self.id if isinstance(id_or_self, cls) else id_or_self
            conn = get_local_db_connection()
            try:
                conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.delete: {e}")
            raise e


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
    def create(cls, data=None, **kwargs):
        """
        新增一筆交易紀錄。
        
        參數:
            data (dict, optional): 包含交易欄位的字典。
            **kwargs: 可選的關鍵字引數。
        
        傳回值:
            HeartTransaction: 新增的交易紀錄物件。
        """
        try:
            if isinstance(data, dict):
                sender_id = data.get('sender_id')
                receiver_id = data.get('receiver_id')
                heart_amount = data.get('heart_amount')
                thank_you_message = data.get('thank_you_message')
            else:
                sender_id = data if data is not None else kwargs.get('sender_id')
                receiver_id = kwargs.get('receiver_id')
                heart_amount = kwargs.get('heart_amount')
                thank_you_message = kwargs.get('thank_you_message')

            now = datetime.datetime.now().isoformat()
            conn = get_local_db_connection()
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
        except Exception as e:
            print(f"Error in HeartTransaction.create: {e}")
            raise e

    @classmethod
    def transfer_hearts(cls, sender_id, receiver_id, amount, message=None):
        """
        原子性地扣除發送者愛心值、增加接收者人氣值，並新增一筆交易紀錄。
        
        參數:
            sender_id (int): 發送者 ID。
            receiver_id (int): 接收者 ID。
            amount (int): 轉移的愛心值。
            message (str, optional): 感謝留言。
            
        傳回值:
            bool: 交易成功傳回 True，否則 raise 異常。
        """
        try:
            if sender_id == receiver_id:
                raise ValueError("Cannot transfer heart values to yourself.")
            if amount <= 0:
                raise ValueError("Transfer amount must be positive.")
            if not message or len(message.strip()) < 5:
                raise ValueError("感謝原因為必填，且長度至少需要 5 個字！")

            now = datetime.datetime.now().isoformat()
            conn = get_local_db_connection()
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
        except Exception as e:
            print(f"Error in HeartTransaction.transfer_hearts: {e}")
            raise e

    @classmethod
    def get_by_id(cls, transaction_id):
        """
        取得單筆交易記錄（依 ID）。
        
        參數:
            transaction_id (int): 交易 ID。
            
        傳回值:
            HeartTransaction: 交易物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
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
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in HeartTransaction.get_by_id: {e}")
            raise e

    @classmethod
    def get_all(cls):
        """
        取得所有交易記錄。
        
        傳回值:
            list: 包含所有 HeartTransaction 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT t.*, u1.name AS sender_name, u2.name AS receiver_name
                    FROM heart_transactions t
                    JOIN users u1 ON t.sender_id = u1.id
                    JOIN users u2 ON t.receiver_id = u2.id
                    ORDER BY t.created_at DESC;
                    """
                ).fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in HeartTransaction.get_all: {e}")
            raise e

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        取得特定使用者的所有交易記錄。
        
        參數:
            user_id (int): 使用者 ID。
            
        傳回值:
            list: 包含 HeartTransaction 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
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
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in HeartTransaction.get_by_user_id: {e}")
            raise e

    @classmethod
    def update(cls, id_or_self, data=None):
        """
        更新交易記錄。支援物件導向式與類別層級。
        
        參數:
            id_or_self (int/HeartTransaction): 交易 ID 或物件。
            data (dict, optional): 欲更新欄位的字典。
            
        傳回值:
            bool: 更新成功傳回 True，否則傳回 False。
        """
        try:
            conn = get_local_db_connection()
            try:
                if isinstance(id_or_self, cls):
                    self = id_or_self
                    conn.execute(
                        """
                        UPDATE heart_transactions
                        SET sender_id = ?, receiver_id = ?, heart_amount = ?, thank_you_message = ?
                        WHERE id = ?;
                        """,
                        (self.sender_id, self.receiver_id, self.heart_amount, self.thank_you_message, self.id)
                    )
                    conn.commit()
                    return True
                else:
                    transaction_id = id_or_self
                    if not data:
                        return False
                    
                    fields = []
                    params = []
                    for key, val in data.items():
                        if key in ('sender_id', 'receiver_id', 'heart_amount', 'thank_you_message'):
                            fields.append(f"{key} = ?")
                            params.append(val)
                    
                    if not fields:
                        return False
                    
                    params.append(transaction_id)
                    sql = f"UPDATE heart_transactions SET {', '.join(fields)} WHERE id = ?;"
                    conn.execute(sql, tuple(params))
                    conn.commit()
                    return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in HeartTransaction.update: {e}")
            raise e

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


class UserBadge:
    def __init__(self, id, user_id, badge_name, badge_icon, badge_description, unlocked_at):
        self.id = id
        self.user_id = user_id
        self.badge_name = badge_name
        self.badge_icon = badge_icon
        self.badge_description = badge_description
        self.unlocked_at = unlocked_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            badge_name=row['badge_name'],
            badge_icon=row['badge_icon'],
            badge_description=row['badge_description'],
            unlocked_at=row['unlocked_at']
        )

    @classmethod
    def create(cls, user_id, badge_name, badge_icon, badge_description):
        """
        Creates a new badge for a user if it doesn't already exist.
        """
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO user_badges (user_id, badge_name, badge_icon, badge_description, unlocked_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (user_id, badge_name, badge_icon, badge_description, now)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Retrieves all badges unlocked by a user.
        """
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM user_badges WHERE user_id = ? ORDER BY unlocked_at DESC;", (user_id,)).fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def check_and_award_badges(cls, user_id):
        """
        Checks if a user meets the criteria for any badges and awards them.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Get start of the current week (Monday 00:00:00)
            now = datetime.datetime.now()
            start_of_week = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_week_iso = start_of_week.isoformat()

            # 1. Novice Helper (新手互助者) - Received at least 1 heart transaction
            received_count = cursor.execute(
                "SELECT COUNT(*) as count FROM heart_transactions WHERE receiver_id = ?;", (user_id,)
            ).fetchone()['count']
            if received_count >= 1:
                cls.create(
                    user_id=user_id,
                    badge_name="新手互助者",
                    badge_icon="fa-handshake text-success",
                    badge_description="成功收到同學發送的第 1 顆愛心！"
                )

            # 2. Campus Good Samaritan (校園好人好事) - Popularity >= 10
            user_row = cursor.execute("SELECT popularity FROM users WHERE id = ?;", (user_id,)).fetchone()
            if user_row and user_row['popularity'] >= 10:
                cls.create(
                    user_id=user_id,
                    badge_name="校園好人好事",
                    badge_icon="fa-heart text-danger",
                    badge_description="累積人氣值（收到愛心數）達到 10 顆以上！"
                )

            # 3. Info Sharing Master (資訊分享達人) - Posted >= 5 lost/found items
            posted_count = cursor.execute(
                "SELECT COUNT(*) as count FROM items WHERE user_id = ?;", (user_id,)
            ).fetchone()['count']
            if posted_count >= 5:
                cls.create(
                    user_id=user_id,
                    badge_name="資訊分享達人",
                    badge_icon="fa-share-nodes text-primary",
                    badge_description="累計發布失物招領公告達 5 篇以上！"
                )

            # 4. Enthusiastic Helper (熱心小幫手) - This Week's Mission
            # - Help classmate once this week (receive 1 transaction)
            received_this_week = cursor.execute(
                "SELECT COUNT(*) as count FROM heart_transactions WHERE receiver_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['count']
            
            # - Share campus info twice this week (post 2 lost/found items)
            posted_this_week = cursor.execute(
                "SELECT COUNT(*) as count FROM items WHERE user_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['count']
            
            # - Receive 3 hearts this week (sum of heart_amount >= 3)
            hearts_this_week = cursor.execute(
                "SELECT SUM(heart_amount) as total FROM heart_transactions WHERE receiver_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['total'] or 0

            if received_this_week >= 1 and posted_this_week >= 2 and hearts_this_week >= 3:
                cls.create(
                    user_id=user_id,
                    badge_name="熱心小幫手",
                    badge_icon="fa-medal text-warning",
                    badge_description="完成本週任務（幫助同學 1 次、分享校園資訊 2 篇、收到 3 顆愛心）。"
                )
            return True
        except Exception as e:
            print(f"Error checking badges for user {user_id}: {e}")
            return False
        finally:
            conn.close()
