"""
使用者與愛心模組 (User & Heart Route Implementation)
處理個人檔案、愛心排行榜、QR Code 掃描、愛心值轉移與徽章管理。
"""

import os
import socket
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from app.models.user import User, HeartTransaction, Badge
from app.models.db import get_db_connection

# 建立使用者與愛心 Blueprint
user_bp = Blueprint("user", __name__)


def login_required(f):
    """
    自訂的登入驗證裝飾器。
    """
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("請先登入後再進行此操作！", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_local_ip():
    """
    獲取本機在區域網路中的 IP，方便手機進行 QR Code 掃描連線。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


@user_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """
    個人檔案頁面。
    """
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    if not user:
        session.clear()
        flash("找不到該使用者，請重新登入。", "danger")
        return redirect(url_for("auth.login"))

    # 1. 檢查並自動發放符合條件的新徽章
    newly_awarded = Badge.check_and_award(user_id)
    for badge in newly_awarded:
        flash(f"🎉 恭喜！您達成了條件，獲得了新徽章：【{badge.icon} {badge.name}】！", "success")

    # 2. 獲取所有已獲得徽章與已釘選徽章
    badges = Badge.get_by_user_id(user_id)
    pinned_badges = Badge.get_pinned_by_user_id(user_id)
    
    # 3. 獲取收發愛心交易歷史紀錄
    transactions = HeartTransaction.get_by_user_id(user_id)

    # 4. 計算排名、傳統徽章與愛心總計資訊 (來自 D1425363 的功能)
    rank = User.get_rank_by_id(user_id)
    legacy_badges = user.get_badges()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(heart_amount) AS total_sent FROM heart_transactions WHERE sender_id = ?;", (user_id,))
    total_sent = cursor.fetchone()['total_sent'] or 0
    cursor.execute("SELECT SUM(heart_amount) AS total_received FROM heart_transactions WHERE receiver_id = ?;", (user_id,))
    total_received = cursor.fetchone()['total_received'] or 0
    conn.close()

    # 5. 生成 QR Code 的 URL，並處理區域網路 IP 轉換
    qr_code_url = url_for('user.qr_transfer', token=user.qr_code_token, _external=True)
    is_local_warning = False
    if "localhost" in qr_code_url or "127.0.0.1" in qr_code_url:
        local_ip = get_local_ip()
        if local_ip != '127.0.0.1':
            qr_code_url = qr_code_url.replace("localhost", local_ip).replace("127.0.0.1", local_ip)
            is_local_warning = True

    return render_template(
        "user/profile.html", 
        user=user, 
        badges=badges, 
        pinned_badges=pinned_badges,
        transactions=transactions,
        qr_code_url=qr_code_url,
        is_local_warning=is_local_warning,
        rank=rank,
        legacy_badges=legacy_badges,
        total_sent=total_sent,
        total_received=total_received
    )


@user_bp.route("/profile/badges/pin", methods=["POST"])
@login_required
def pin_badges():
    """
    自訂釘選徽章 (最多 3 個)。
    """
    user_id = session['user_id']
    selected_badges = request.form.getlist("badges")
    
    if len(selected_badges) > 3:
        flash("最多只能釘選 3 個徽章！", "warning")
        return redirect(url_for("user.profile"))
        
    try:
        Badge.pin_badges(user_id, selected_badges)
        flash("徽章展示櫃更新成功！", "success")
    except Exception as e:
        flash(f"更新徽章展示失敗：{str(e)}", "danger")
        
    return redirect(url_for("user.profile"))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """
    更新個人資料（真實姓名/暱稱、系級、選擇預設頭像或上傳自訂頭像）。
    """
    user_id = session['user_id']
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip() or None
    avatar_choice = request.form.get("avatar_choice", "")
    
    if not name:
        flash("真實姓名 / 暱稱不能為空！", "danger")
        return redirect(url_for('user.profile'))
        
        # 1. 取得當週時間並計算本週互助任務進度
        import datetime
        from app.models.db import get_db_connection
        
        now = datetime.datetime.now()
        start_of_week = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week_iso = start_of_week.isoformat()
        
        conn = get_db_connection()
        try:
            received_this_week = conn.execute(
                "SELECT COUNT(*) as count FROM heart_transactions WHERE receiver_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['count']
            
            posted_this_week = conn.execute(
                "SELECT COUNT(*) as count FROM items WHERE user_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['count']
            
            hearts_this_week = conn.execute(
                "SELECT SUM(heart_amount) as total FROM heart_transactions WHERE receiver_id = ? AND created_at >= ?;",
                (user_id, start_of_week_iso)
            ).fetchone()['total'] or 0
        finally:
            conn.close()

        # 2. 自動檢查與解鎖勳章
        UserBadge.check_and_award_badges(user_id)
        badges = UserBadge.get_by_user_id(user_id)

        # Calculate external QR Code URL targeting the local Wi-Fi IP if loopback/localhost is used
        import socket
        def get_local_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('10.255.255.255', 1))
                IP = s.getsockname()[0]
            except Exception:
                IP = '127.0.0.1'
            finally:
                s.close()
            return IP

        qr_transfer_url = url_for('user.qr_transfer', token=user.qr_code_token, _external=True)
        is_local_warning = False
        if "localhost" in qr_transfer_url or "127.0.0.1" in qr_transfer_url:
            local_ip = get_local_ip()
            if local_ip != '127.0.0.1':
                qr_transfer_url = qr_transfer_url.replace("localhost", local_ip).replace("127.0.0.1", local_ip)
                is_local_warning = True

        return render_template(
            "user/profile.html", 
            user=user, 
            transactions=transactions,
            qr_transfer_url=qr_transfer_url,
            is_local_warning=is_local_warning,
            received_this_week=received_this_week,
            posted_this_week=posted_this_week,
            hearts_this_week=hearts_this_week,
            badges=badges
        )

    update_data = {
        'name': name,
        'department': department
    }
    
    # 處理頭像選擇或上傳
    if avatar_choice == "predefined":
        selected_seed = request.form.get("predefined_seed", "")
        if selected_seed:
            update_data['avatar'] = f"https://api.dicebear.com/7.x/fun-emoji/svg?seed={selected_seed}"
    elif avatar_choice == "upload":
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatar_{user_id}.{ext}"
                    
                    upload_folder = os.path.join(current_app.root_path, 'static', 'images', 'avatars')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    update_data['avatar'] = "images/avatars/" + filename
                else:
                    flash("不支援的檔案格式，僅限 PNG, JPG, JPEG, GIF 或 SVG 圖片。", "danger")
                    return redirect(url_for('user.profile'))
                    
    try:
        User.update(user_id, update_data)
        flash("個人資料已成功更新！", "success")
    except Exception as e:
        flash(f"更新個人資料失敗：{str(e)}", "danger")
        
    return redirect(url_for('user.profile'))


@user_bp.route("/qr/<token>", methods=["GET"])
@login_required
def qr_transfer(token):
    """
    掃描他人 QR Code 後的愛心值轉移頁面。
    """
    current_user_id = session['user_id']
    receiver = User.get_by_qr_code_token(token)
    
    if not receiver:
        flash("此 QR Code 無效！找不到對應的接收者。", "danger")
        return redirect(url_for("user.profile"))
        
    if receiver.id == current_user_id:
        flash("無法對自己進行愛心轉移！", "warning")
        return redirect(url_for("user.profile"))
        
    # 載入接收者釘選的徽章展示在畫面上
    pinned_badges = Badge.get_pinned_by_user_id(receiver.id)
    sender = User.get_by_id(current_user_id)

    return render_template(
        "user/qr_transfer.html", 
        receiver=receiver, 
        pinned_badges=pinned_badges,
        sender=sender
    )


@user_bp.route("/qr/<token>/transfer", methods=["POST"])
@login_required
def transfer(token):
    """
    執行愛心值轉移交易。
    """
    sender_id = session['user_id']
    heart_amount_str = request.form.get("heart_amount", "").strip()
    thank_you_message = request.form.get("thank_you_message", "").strip()

    # 1. 驗證愛心數量欄位
    if not heart_amount_str:
        flash("請輸入要轉移的愛心值數量。", "danger")
        return redirect(url_for('user.qr_transfer', token=token))

    # 2. 驗證感謝留言欄位 (升級需求：給愛心時必須附上原因且大於等於 5 個字)
    if not thank_you_message or len(thank_you_message) < 5:
        flash("發送愛心必須附上至少 5 個字的感謝原因！讓善行被記錄下來吧 💖", "danger")
        return redirect(url_for('user.qr_transfer', token=token))


    receiver = User.get_by_qr_code_token(token)
    
    if not receiver:
        flash("交易失敗：找不到對應的接收者。", "danger")
        return redirect(url_for("user.profile"))
        
    if receiver.id == sender_id:
        flash("交易失敗：無法對自己進行愛心轉移。", "warning")
        return redirect(url_for("user.profile"))

    # 解析並驗證愛心值
    try:
        heart_amount = int(request.form.get("heart_amount", 0))
    except ValueError:
        flash("請輸入有效的整數愛心值！", "warning")
        return redirect(url_for("user.qr_transfer", token=token))
        
    thank_you_message = request.form.get("thank_you_message", "").strip()
    is_anonymous = request.form.get("is_anonymous") == "1"

    if heart_amount <= 0:
        flash("發送數量必須大於 0 顆愛心！", "warning")
        return redirect(url_for("user.qr_transfer", token=token))

    sender = User.get_by_id(sender_id)
    if sender.heart_balance < heart_amount:
        flash(f"愛心值餘額不足！您目前僅剩餘 {sender.heart_balance} 顆愛心。", "danger")
        return redirect(url_for("user.qr_transfer", token=token))

    # 執行轉移
    try:
        HeartTransaction.transfer_hearts(sender_id, receiver.id, heart_amount, thank_you_message, anonymous=is_anonymous)
        
        # 轉移成功後，檢查並發放雙方的徽章 (因為發送者/接收者資料改變)
        Badge.check_and_award(sender_id)
        Badge.check_and_award(receiver.id)
        
        flash(f"成功發送 {heart_amount} 顆愛心給 {receiver.name}！感謝您的熱心協助！", "success")
        return redirect(url_for("user.profile"))
    except Exception as e:
        flash(f"交易失敗，請稍後再試：{str(e)}", "danger")
        return redirect(url_for("user.qr_transfer", token=token))


@user_bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    愛心與人氣排行榜。
    """
    try:
        top_users = User.get_top_by_popularity(limit=10)
        return render_template("user/leaderboard.html", top_users=top_users)
    except Exception as e:
        flash(f"載入排行榜失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))


@user_bp.route("/thanks", methods=["GET"])
def thanks():
    """
    公開感謝牆。
    
    GET:
        - 查詢所有的愛心互動歷史紀錄（僅展示有感謝原因的善行紀錄）。
        - 渲染 `templates/user/thanks.html`。
    """
    try:
        all_transactions = HeartTransaction.get_all()
        # 篩選出有感謝留言且字數大於等於 5 的紀錄
        thanks_list = [t for t in all_transactions if t.thank_you_message and len(t.thank_you_message.strip()) >= 5]
        return render_template("user/thanks.html", thanks_list=thanks_list)
    except Exception as e:
        flash(f"載入感謝牆失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))

    period = request.args.get("period", "total")
    if period not in ("total", "today", "week", "month"):
        period = "total"

    top_users = User.get_top_by_period(period=period, limit=10)
    
    # 載入前十名使用者釘選的徽章
    for user in top_users:
        user.pinned_badges = Badge.get_pinned_by_user_id(user.id)
        
    return render_template("user/leaderboard.html", top_users=top_users, current_period=period)
