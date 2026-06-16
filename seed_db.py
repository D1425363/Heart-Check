from werkzeug.security import generate_password_hash
from app.models.db import init_db, get_db_connection
import datetime
import os

def seed():
    # 1. Initialize tables
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM user_badges;")
    cursor.execute("DELETE FROM item_comments;")
    cursor.execute("DELETE FROM announcements;")
    cursor.execute("DELETE FROM items;")
    cursor.execute("DELETE FROM heart_transactions;")
    cursor.execute("DELETE FROM users;")
    
    print("Seeding database...")
    
    # 2. Add users
    pwd_hash = generate_password_hash("password123")
    
    users = [
        ("admin", pwd_hash, "管理員 (宿舍幹部)", "S000000", "資訊工程系", 500, 250, "token_admin"),
        ("hero", pwd_hash, "熱心同學小明", "S001001", "電機工程系", 80, 999, "token_hero"),
        ("finder", pwd_hash, "失物獵人小華", "S001002", "企業管理系", 120, 150, "token_finder"),
        ("user", pwd_hash, "普通學生阿強", "S001003", "生活應用科學系", 100, 0, "token_user")
    ]
    
    now = datetime.datetime.now()
    now_iso = now.isoformat()
    
    for username, p_hash, name, student_id, dept, hearts, pop, token in users:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (username, p_hash, name, student_id, dept, hearts, pop, token, now_iso, now_iso)
        )
    
    conn.commit()
    
    # Get user IDs
    cursor.execute("SELECT id, username FROM users;")
    user_map = {r['username']: r['id'] for r in cursor.fetchall()}
    
    # 3. Add transactions at different time periods to test leaderboard filters:
    # Today, 3 days ago (this week), 10 days ago (this month), and 45 days ago (older)
    today_time = now.isoformat()
    three_days_ago = (now - datetime.timedelta(days=1)).isoformat()
    ten_days_ago = (now - datetime.timedelta(days=10)).isoformat()
    forty_five_days_ago = (now - datetime.timedelta(days=45)).isoformat()
    
    transactions = [
        # Today: user -> hero (20 hearts)
        (user_map["user"], user_map["hero"], 20, "謝謝小明今天幫我搬宿舍行李，非常熱心！", today_time),
        # This week (3 days ago): finder -> hero (30 hearts)
        (user_map["finder"], user_map["hero"], 30, "感謝在排球場幫我撿到學生證並送回！", three_days_ago),
        # This month (10 days ago): admin -> finder (15 hearts)
        (user_map["admin"], user_map["finder"], 15, "感謝協助籌辦宿舍消防演練！", ten_days_ago),
        # Older (45 days ago): hero -> finder (25 hearts)
        (user_map["hero"], user_map["finder"], 25, "感謝上個月借我微積分課本複習！", forty_five_days_ago)
    ]
    
    for sender, receiver, amt, msg, ttime in transactions:
        cursor.execute(
            """
            INSERT INTO heart_transactions (sender_id, receiver_id, heart_amount, thank_you_message, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (sender, receiver, amt, msg, ttime)
        )
        
    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
