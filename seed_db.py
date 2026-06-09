from werkzeug.security import generate_password_hash
from app.models.db import init_db, get_db_connection
import datetime
import os

def seed():
    # 1. Initialize tables
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we already have users
    cursor.execute("SELECT COUNT(*) AS count FROM users;")
    row = cursor.fetchone()
    count = row['count']
    if count > 0:
        print("Database already has data. Skipping seed.")
        conn.close()
        return
        
    print("Seeding database...")
    
    # 2. Add users
    # Password is password123 for all users
    pwd_hash = generate_password_hash("password123")
    
    users = [
        ("admin", pwd_hash, "管理員 (宿舍幹部)", "S000000", "資訊工程系", 500, 250, "token_admin"),
        ("hero", pwd_hash, "熱心同學小明", "S001001", "電機工程系", 80, 999, "token_hero"),
        ("finder", pwd_hash, "失物獵人小華", "S001002", "企業管理系", 120, 150, "token_finder"),
        ("user", pwd_hash, "普通學生阿強", "S001003", "生活應用科學系", 100, 0, "token_user")
    ]
    
    now = datetime.datetime.now().isoformat()
    
    for username, p_hash, name, student_id, dept, hearts, pop, token in users:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (username, p_hash, name, student_id, dept, hearts, pop, token, now, now)
        )
    
    conn.commit()
    
    # Get user IDs
    cursor.execute("SELECT id, username FROM users;")
    user_map = {r['username']: r['id'] for r in cursor.fetchall()}
    
    # 3. Add announcements
    announcements = [
        ("宿舍 A 棟熱水器緊急維修公告", "各位宿生好，宿舍 A 棟 3 樓與 4 樓的熱水器因感應器故障，將於明日上午 9:00 至 12:00 進行停水維修，期間將暫停熱水供應，請宿生多加留意，造成不便敬請見諒。", "dorm", user_map["admin"]),
        ("115 學年度畢業典禮「愛心服務隊」志工招募中！", "歡迎各位熱心的同學加入畢業典禮服務隊！本次志工服務可折抵服務學習時數 6 小時，並可獲得 Heart Check 平台贈送的 50 點愛心值！歡迎至課外活動組報名，一起為學長姐留下美好的畢業回憶！", "campus", user_map["admin"]),
        ("學餐二樓消防安檢通知", "本週五下午 2:00 起學餐二樓將進行例行性消防安全設備檢測，屆時警報器可能會短暫響起，請二樓各店家與用餐同學配合，切勿驚慌。", "campus", user_map["admin"])
    ]
    
    for title, content, cat, author_id in announcements:
        cursor.execute(
            """
            INSERT INTO announcements (title, content, category, author_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (title, content, cat, author_id, now, now)
        )
        
    # 4. Add Lost & Found items
    items = [
        ("在學餐遺失藍色太和工房水壺", "今天中午 12:30 左右在學餐二樓靠窗座位用餐，離開時不小心把一個藍色太和工房的水壺（上面有貓咪貼紙）忘在桌上了。如果有同學撿到，拜託聯繫我，這是我很重要的生日禮物，非常感謝！", None, "學校餐廳二樓", "lost", "unclaimed", user_map["user"], "手機：0912-345-678 阿強"),
        ("在圖書館二樓拾獲 AirPods Pro 耳機", "下午 3:15 在圖書館二樓檢索區的 5 號電腦桌上撿到一個 AirPods Pro 耳機（有綠色矽膠保護套），已先交給圖書館一樓服務台。請失主攜帶證明或當場配對認領！", None, "圖書館二樓檢索區", "found", "unclaimed", user_map["finder"], "已送至圖書館服務台"),
        ("在體育館羽球場撿到一把黑色皮夾", "昨晚 8 點在羽球場 B 場地的休息長椅上拾獲一把黑色皮夾，裡面有學生證（張同學）及少量現金。請失主用站內信或電話聯絡我，或直接到體育組認領，我會把皮夾交過去。", None, "體育館羽球場", "found", "unclaimed", user_map["hero"], "電話：0987-654-321 小明")
    ]
    
    for title, desc, img, loc, itype, status, uid, cinfo in items:
        cursor.execute(
            """
            INSERT INTO items (title, description, image_url, location, item_type, status, user_id, contact_info, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (title, desc, img, loc, itype, status, uid, cinfo, now, now)
        )
        
    # 5. Add transactions
    transactions = [
        (user_map["user"], user_map["hero"], 20, "謝謝小明同學昨天幫我搬宿舍行李，非常熱心！", now),
        (user_map["finder"], user_map["hero"], 30, "感謝在排球場幫我撿到學生證並送回，大感謝！", now)
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
