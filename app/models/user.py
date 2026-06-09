import datetime
import secrets
from app.models.db import get_db_connection

class User:
    def __init__(self, id, username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at, avatar=''):
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
        self.avatar = avatar

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        avatar = row['avatar'] if 'avatar' in row.keys() else ''
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
            updated_at=row['updated_at'],
            avatar=avatar
        )

    @classmethod
    def create(cls, username, password_hash, name, student_id, department=None, heart_balance=100, popularity=0, qr_code_token=None, avatar=''):
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
                INSERT INTO users (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, avatar, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, avatar, now, now)
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
    def get_rank_by_id(cls, user_id):
        """
        Calculates user rank based on popularity.
        """
        try:
            conn = get_db_connection()
            try:
                row = conn.execute("SELECT popularity, name, id FROM users WHERE id = ?;", (user_id,)).fetchone()
                if not row:
                    return None
                pop = row['popularity']
                name = row['name']
                uid = row['id']
                
                count_row = conn.execute(
                    """
                    SELECT COUNT(*) + 1 AS rank
                    FROM users
                    WHERE popularity > ? 
                       OR (popularity = ? AND name < ?) 
                       OR (popularity = ? AND name = ? AND id < ?);
                    """,
                    (pop, pop, name, pop, name, uid)
                ).fetchone()
                return count_row['rank'] if count_row else None
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in User.get_rank_by_id: {e}")
            return None

    def get_badges(self):
        """
        Returns badges check for backward compatibility with D1425363.
        """
        badges = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 1. 新手上路 (Newbie)
            badges.append({
                'id': 'newbie',
                'name': '新手上路',
                'description': '註冊並加入 Heart Check 互助平台',
                'icon': 'fa-solid fa-baby',
                'color': '#ffbe0b',
                'unlocked': True,
                'progress': '1/1'
            })
            
            # 2. 慷慨大使 (Generous Ambassador) - sent hearts count >= 3
            cursor.execute("SELECT COUNT(*) AS count FROM heart_transactions WHERE sender_id = ?;", (self.id,))
            sent_count = cursor.fetchone()['count']
            badges.append({
                'id': 'ambassador',
                'name': '慷慨大使',
                'description': '累計送出愛心次數達到 3 次',
                'icon': 'fa-solid fa-hand-holding-heart',
                'color': '#ff4b72',
                'unlocked': sent_count >= 3,
                'progress': f"{sent_count}/3"
            })
            
            # 3. 人氣焦點 (Popularity Star) - received popularity >= 50
            badges.append({
                'id': 'star',
                'name': '人氣焦點',
                'description': '累積人氣值達到 50 以上',
                'icon': 'fa-solid fa-fire',
                'color': '#ff9f1c',
                'unlocked': self.popularity >= 50,
                'progress': f"{self.popularity}/50"
            })
            
            # 4. 熱心助人 (Helping Hand) - items reported >= 2
            cursor.execute("SELECT COUNT(*) AS count FROM items WHERE user_id = ?;", (self.id,))
            items_count = cursor.fetchone()['count']
            badges.append({
                'id': 'helper',
                'name': '熱心助人',
                'description': '累計發布失物招領達 2 次',
                'icon': 'fa-solid fa-handshake-angle',
                'color': '#4ea8de',
                'unlocked': items_count >= 2,
                'progress': f"{items_count}/2"
            })
            
            # 5. 愛心富豪 (Heart Tycoon) - current heart balance >= 200
            badges.append({
                'id': 'tycoon',
                'name': '愛心富豪',
                'description': '持有愛心餘額達到 200 以上',
                'icon': 'fa-solid fa-gem',
                'color': '#7209b7',
                'unlocked': self.heart_balance >= 200,
                'progress': f"{self.heart_balance}/200"
            })
            
            # 6. 宿舍之光 (Light of Dorm) - sent/received transactions with message containing 宿舍/寢室
            cursor.execute(
                """
                SELECT COUNT(*) AS count 
                FROM heart_transactions 
                WHERE (sender_id = ? OR receiver_id = ?) 
                  AND (thank_you_message LIKE '%宿舍%' OR thank_you_message LIKE '%寢室%');
                """, 
                (self.id, self.id)
            )
            dorm_count = cursor.fetchone()['count']
            badges.append({
                'id': 'dorm',
                'name': '宿舍之光',
                'description': '在宿舍互助中獲得或發送愛心回饋',
                'icon': 'fa-solid fa-house-chimney-window',
                'color': '#f72585',
                'unlocked': dorm_count >= 1,
                'progress': f"{dorm_count}/1"
            })
            
            conn.close()
        except Exception as e:
            print(f"Error in User.get_badges: {e}")
        return badges

    @classmethod
    def update(cls, id_or_self, data=None):
        """
        Updates user records. Supports both object-oriented updates and class-level dynamic updates.
        """
        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        try:
            if isinstance(id_or_self, cls):
                # Object-oriented update
                self = id_or_self
                self.updated_at = now
                conn.execute(
                    """
                    UPDATE users 
                    SET username = ?, password_hash = ?, name = ?, student_id = ?, department = ?, 
                        heart_balance = ?, popularity = ?, qr_code_token = ?, avatar = ?, updated_at = ?
                    WHERE id = ?;
                    """,
                    (self.username, self.password_hash, self.name, self.student_id, self.department,
                     self.heart_balance, self.popularity, self.qr_code_token, self.avatar, self.updated_at, self.id)
                )
                conn.commit()
                return True
            else:
                # Class-level dynamic update
                user_id = id_or_self
                if not data:
                    return False
                
                fields = []
                params = []
                for key, val in data.items():
                    if key in ('username', 'password_hash', 'name', 'student_id', 'department', 'heart_balance', 'popularity', 'qr_code_token', 'avatar'):
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

    def update_instance(self):
        """
        Instance method version of update.
        """
        return User.update(self)

    def update_object(self):
        return User.update(self)

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
        
        # Optional joined fields
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
    def create(cls, sender_id, receiver_id, heart_amount, thank_you_message=None):
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
        if sender_id == receiver_id:
            raise ValueError("Cannot transfer heart values to yourself.")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        now = datetime.datetime.now().isoformat()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sender_row = cursor.execute("SELECT heart_balance FROM users WHERE id = ?;", (sender_id,)).fetchone()
            if not sender_row:
                raise ValueError("Sender user not found.")
            
            if sender_row['heart_balance'] < amount:
                raise ValueError("Insufficient heart balance.")

            receiver_exists = cursor.execute("SELECT 1 FROM users WHERE id = ?;", (receiver_id,)).fetchone()
            if not receiver_exists:
                raise ValueError("Receiver user not found.")

            cursor.execute(
                "UPDATE users SET heart_balance = heart_balance - ?, updated_at = ? WHERE id = ?;",
                (amount, now, sender_id)
            )

            cursor.execute(
                "UPDATE users SET popularity = popularity + ?, updated_at = ? WHERE id = ?;",
                (amount, now, receiver_id)
            )

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
            conn.execute("UPDATE user_badges SET is_pinned = 0 WHERE user_id = ?;", (user_id,))
            if badge_types:
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
        conn = get_db_connection()
        new_awards = []
        try:
            existing_rows = conn.execute("SELECT badge_type FROM user_badges WHERE user_id = ?;", (user_id,)).fetchall()
            existing_badges = {row['badge_type'] for row in existing_rows}

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
