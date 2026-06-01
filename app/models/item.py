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
        print(f"Error establishing database connection in Item model: {e}")
        raise e

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
    def create(cls, data=None, **kwargs):
        """
        新增一筆失物招領物件記錄。
        
        參數:
            data (dict, optional): 包含物件欄位的字典。
            **kwargs: 可選的關鍵字引數。
        
        傳回值:
            Item: 新增的物件。
        """
        try:
            if isinstance(data, dict):
                title = data.get('title')
                description = data.get('description')
                location = data.get('location')
                item_type = data.get('item_type')
                status = data.get('status', 'unclaimed')
                user_id = data.get('user_id')
                image_url = data.get('image_url')
                contact_info = data.get('contact_info')
            else:
                title = data if data is not None else kwargs.get('title')
                description = kwargs.get('description')
                location = kwargs.get('location')
                item_type = kwargs.get('item_type')
                status = kwargs.get('status', 'unclaimed')
                user_id = kwargs.get('user_id')
                image_url = kwargs.get('image_url')
                contact_info = kwargs.get('contact_info')

            if item_type not in ('lost', 'found'):
                raise ValueError("item_type must be either 'lost' or 'found'.")
            if status not in ('unclaimed', 'claimed'):
                raise ValueError("status must be either 'unclaimed' or 'claimed'.")
            if not user_id:
                raise ValueError("user_id is required.")

            now = datetime.datetime.now().isoformat()
            conn = get_local_db_connection()
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
        except Exception as e:
            print(f"Error in Item.create: {e}")
            raise e

    @classmethod
    def get_by_id(cls, item_id):
        """
        取得單筆物件記錄（依 ID）。
        
        參數:
            item_id (int): 物品 ID。
            
        傳回值:
            Item: 物品物件，若不存在則傳回 None。
        """
        try:
            conn = get_local_db_connection()
            try:
                row = conn.execute(
                    """
                    SELECT i.*, u.name AS user_name
                    FROM items i
                    JOIN users u ON i.user_id = u.id
                    WHERE i.id = ?;
                    """,
                    (item_id,)
                ).fetchone()
                return cls.from_row(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.get_by_id: {e}")
            raise e

    @classmethod
    def get_all(cls):
        """
        取得所有物件記錄（依建立時間降冪排序）。
        
        傳回值:
            list: 包含所有 Item 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT i.*, u.name AS user_name
                    FROM items i
                    JOIN users u ON i.user_id = u.id
                    ORDER BY i.created_at DESC;
                    """
                ).fetchall()
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.get_all: {e}")
            raise e

    @classmethod
    def get_by_type(cls, item_type):
        """
        依分類取得物件記錄（lost/found）。
        
        參數:
            item_type (str): 'lost' 或 'found'。
            
        傳回值:
            list: 包含 Item 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
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
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.get_by_type: {e}")
            raise e

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        取得特定使用者發布的所有物件記錄。
        
        參數:
            user_id (int): 使用者 ID。
            
        傳回值:
            list: 包含 Item 物件的列表。
        """
        try:
            conn = get_local_db_connection()
            try:
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
                return [cls.from_row(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.get_by_user_id: {e}")
            raise e

    @classmethod
    def update(cls, id_or_self, data=None):
        """
        更新物件記錄。支援物件導向式更新與類別層級更新。
        
        參數:
            id_or_self (int/Item): 物品 ID 或 Item 物件。
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
                    if self.item_type not in ('lost', 'found'):
                        raise ValueError("item_type must be either 'lost' or 'found'.")
                    if self.status not in ('unclaimed', 'claimed'):
                        raise ValueError("status must be either 'unclaimed' or 'claimed'.")
                    self.updated_at = now
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
                else:
                    # 類別層級更新
                    item_id = id_or_self
                    if not data:
                        return False
                    
                    # 驗證特定欄位
                    if 'item_type' in data and data['item_type'] not in ('lost', 'found'):
                        raise ValueError("item_type must be either 'lost' or 'found'.")
                    if 'status' in data and data['status'] not in ('unclaimed', 'claimed'):
                        raise ValueError("status must be either 'unclaimed' or 'claimed'.")

                    fields = []
                    params = []
                    for key, val in data.items():
                        if key in ('title', 'description', 'image_url', 'location', 'item_type', 'status', 'user_id', 'contact_info'):
                            fields.append(f"{key} = ?")
                            params.append(val)
                    
                    if not fields:
                        return False
                    
                    fields.append("updated_at = ?")
                    params.append(now)
                    params.append(item_id)
                    
                    sql = f"UPDATE items SET {', '.join(fields)} WHERE id = ?;"
                    conn.execute(sql, tuple(params))
                    conn.commit()
                    return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.update: {e}")
            raise e

    @classmethod
    def delete(cls, id_or_self):
        """
        刪除物件記錄。支援物件導向式與類別層級。
        
        參數:
            id_or_self (int/Item): 物品 ID 或 Item 物件。
            
        傳回值:
            bool: 刪除成功傳回 True，否則傳回 False。
        """
        try:
            item_id = id_or_self.id if isinstance(id_or_self, cls) else id_or_self
            conn = get_local_db_connection()
            try:
                conn.execute("DELETE FROM items WHERE id = ?;", (item_id,))
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in Item.delete: {e}")
            raise e
