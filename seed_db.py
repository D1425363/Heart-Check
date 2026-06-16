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
            INSERT OR IGNORE INTO users (username, password_hash, name, student_id, department, heart_balance, popularity, qr_code_token, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (username, p_hash, name, student_id, dept, hearts, pop, token, now_iso, now_iso)
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
            (title, content, cat, author_id, now_iso, now_iso)
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
            (title, desc, img, loc, itype, status, uid, cinfo, now_iso, now_iso)
        )
        
    # Helper to calculate relative times
    def days_ago(n):
        return (now - datetime.timedelta(days=n)).isoformat()

    transactions = [
        (user_map["user"], user_map["hero"], 20, "謝謝小明同學今天幫我搬行李，非常熱心！", days_ago(0), 1), # 匿名交易
        # Change days_ago(3) to days_ago(1) to make it fall within the current week for leaderboard testing
        (user_map["finder"], user_map["hero"], 30, "感謝在排球場幫我撿到學生證並送回，大感謝！", days_ago(1), 0),
        (user_map["admin"], user_map["hero"], 50, "感謝協助宿舍消防演練的引導！", days_ago(10), 0),
        (user_map["user"], user_map["hero"], 15, "感謝分享昨天的微積分筆記，太強了！", days_ago(18), 0),
        (user_map["finder"], user_map["hero"], 25, "感謝在雨天借我雨傘，好人一生平安！", days_ago(35), 0),
        (user_map["admin"], user_map["hero"], 40, "感謝幹部會議上的熱烈發言與建議！", days_ago(50), 0),
        (user_map["user"], user_map["hero"], 60, "感謝上學期期末考前一週的宿舍夜讀指導！", days_ago(75), 0),
        
        (user_map["hero"], user_map["finder"], 20, "謝謝幫我帶午餐，真的超方便！", days_ago(5), 0),
        (user_map["hero"], user_map["user"], 30, "感謝幫忙看照房間，我回家那幾天多虧有你！", days_ago(22), 0),
        (user_map["hero"], user_map["admin"], 15, "感謝宿舍幹部協助處理熱水器漏水問題！", days_ago(60), 0),
        
        (user_map["finder"], user_map["user"], 10, "感謝在走廊借我原子筆用！", days_ago(40), 0),
        (user_map["admin"], user_map["finder"], 25, "感謝幫忙張貼校園健康週海報！", days_ago(12), 0)
    ]
    
    for sender, receiver, amt, msg, ttime, anon in transactions:
        cursor.execute(
            """
            INSERT INTO heart_transactions (sender_id, receiver_id, heart_amount, thank_you_message, is_anonymous, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (sender, receiver, amt, msg, anon, ttime)
        )

    # 6. Add Help Requests
    help_requests = [
        (user_map["user"], "notes", "求微積分二的期中考筆記", "我們下週三要期中考了，希望有電機或資工系修過張教授微積分二的學長姐能分享筆記，可以用 10 顆愛心作為回報！", "open"),
        (user_map["finder"], "team", "徵求大專盃羽球賽混雙隊友", "尋找一位有羽球底子的女同學一起組隊打大專盃混雙。每週二、四晚上在體育館練習，有興趣請私訊我聯絡方式！", "open"),
        (user_map["hero"], "lost", "在宿舍大廳遺失一把紅色雨傘", "昨天下午下大雨時，把雨傘放在一樓大廳傘架，傍晚要拿時發現不見了。雨傘是自動摺疊傘，手把上有一個小刮痕。若有同學誤拿，請放回原位，感激不盡！", "open"),
        (user_map["user"], "textbook", "求購「計算機概論」二手書", "大一計算機概論課程需要用書：Computer Science: An Overview。希望書況良好、無過多塗鴉，價格可議。可用愛心或實體請飲料答謝！", "open"),
        (user_map["finder"], "course", "請問有人修過陳教授的「演算法」嗎？", "想請問這門課的評分標準如何？期中跟期末考會不會很硬？是否需要先修什麼科目？感謝分享經驗的學長姐！", "resolved")
    ]
    
    for uid, cat, title, desc, status in help_requests:
        cursor.execute(
            """
            INSERT INTO help_requests (user_id, category, title, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (uid, cat, title, desc, status, now_iso, now_iso)
        )
        
    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
