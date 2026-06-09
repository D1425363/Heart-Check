"""
使用者與愛心模組 (User & Heart Route Skeleton)
處理個人檔案、愛心排行榜、QR Code 掃描與愛心值轉移。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, current_app
import os
from app.models.user import User, HeartTransaction
from app.models.db import get_db_connection

# 建立使用者與愛心 Blueprint
user_bp = Blueprint("user", __name__)


@user_bp.route("/profile", methods=["GET"])
def profile():
    """
    個人檔案頁面。
    
    GET:
        - 檢查登入狀態。
        - 讀取當前使用者的愛心值餘額、人氣值與交易歷史紀錄。
        - 計算排名與徽章成就。
        - 渲染 `templates/user/profile.html` 並提供專屬 QR Code。
    """
    if 'user_id' not in session:
        flash("請先登入後再進行此操作。", "warning")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    try:
        user = User.get_by_id(user_id)
        if not user:
            # Session 中有 ID 但資料庫找不到，表示使用者可能被刪除
            session.clear()
            flash("使用者不存在，請重新登入。", "danger")
            return redirect(url_for('auth.login'))

        transactions = HeartTransaction.get_by_user_id(user_id)
        
        # Calculate rank and badges
        rank = User.get_rank_by_id(user_id)
        badges = user.get_badges()

        # Calculate detailed heart statistics
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(heart_amount) AS total_sent FROM heart_transactions WHERE sender_id = ?;", (user_id,))
        total_sent = cursor.fetchone()['total_sent'] or 0
        cursor.execute("SELECT SUM(heart_amount) AS total_received FROM heart_transactions WHERE receiver_id = ?;", (user_id,))
        total_received = cursor.fetchone()['total_received'] or 0
        conn.close()
        
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
            rank=rank,
            badges=badges,
            total_sent=total_sent,
            total_received=total_received
        )
    except Exception as e:
        flash(f"載入個人檔案失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_bp.route("/profile/update", methods=["POST"])
def update_profile():
    """
    更新個人資料（真實姓名/暱稱、系級、選擇預設頭像或上傳自訂頭像）。
    """
    if 'user_id' not in session:
        flash("請先登入後再進行此操作。", "warning")
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip() or None
    avatar_choice = request.form.get("avatar_choice", "")
    
    if not name:
        flash("真實姓名 / 暱稱不能為空！", "danger")
        return redirect(url_for('user.profile'))
        
    update_data = {
        'name': name,
        'department': department
    }
    
    # Handle avatar selection/upload
    if avatar_choice == "predefined":
        selected_seed = request.form.get("predefined_seed", "")
        if selected_seed:
            update_data['avatar'] = f"https://api.dicebear.com/7.x/fun-emoji/svg?seed={selected_seed}"
    elif avatar_choice == "upload":
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Save custom avatar to static/images/avatars
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatar_{user_id}_{int(os.path.getmtime(__file__))}.{ext}"
                    
                    upload_folder = os.path.join(current_app.root_path, 'static', 'images', 'avatars')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    update_data['avatar'] = filename
                else:
                    flash("不支援的檔案格式，請上傳 PNG, JPG, JPEG, GIF 或 SVG 格式的圖片。", "danger")
                    return redirect(url_for('user.profile'))
                    
    try:
        User.update(user_id, update_data)
        session['user_name'] = name  # Update the name in session
        flash("個人資料已成功更新！", "success")
    except Exception as e:
        flash(f"更新個人資料失敗：{str(e)}", "danger")
        
    return redirect(url_for('user.profile'))


@user_bp.route("/qr/<token>", methods=["GET"])
def qr_transfer(token):
    """
    掃描他人 QR Code 後的愛心值轉移頁面。
    
    GET:
        - 根據 token 查詢接收者（幫助者）名稱。
        - 確保當前登入者與接收者不同。
        - 渲染 `templates/user/qr_transfer.html` 提供留言與愛心值輸入。
    """
    if 'user_id' not in session:
        flash("請先登入後再進行掃描轉移操作。", "warning")
        return redirect(url_for('auth.login'))

    current_user_id = session['user_id']
    try:
        receiver = User.get_by_qr_code_token(token)
        if not receiver:
            # 找不到該 Token 對應的使用者，回傳 404
            abort(404, description="此 QR Code 無效或不存在。")

        if receiver.id == current_user_id:
            flash("您無法發送愛心給自己！", "warning")
            return redirect(url_for('user.profile'))

        return render_template("user/qr_transfer.html", receiver=receiver, token=token)
    except Exception as e:
        flash(f"處理 QR Code 發生錯誤：{str(e)}", "danger")
        return redirect(url_for('user.profile'))


@user_bp.route("/qr/<token>/transfer", methods=["POST"])
def transfer(token):
    """
    執行愛心值轉移交易。
    
    POST:
        - 接收表單欄位：heart_amount, thank_you_message。
        - 處理邏輯：
            1. 檢查當前登入者餘額是否足夠。
            2. 啟動資料庫 Transaction，扣除發送者愛心值、增加接收者人氣值，並新增一筆交易紀錄至 heart_transactions 表。
            3. 重導向至 `/profile` 頁面。
        - 錯誤處理：
            - 餘額不足或數值不合法：重導向回轉移頁面並顯示警告訊息。
    """
    if 'user_id' not in session:
        flash("請先登入後再進行轉移。", "warning")
        return redirect(url_for('auth.login'))

    sender_id = session['user_id']
    heart_amount_str = request.form.get("heart_amount", "").strip()
    thank_you_message = request.form.get("thank_you_message", "").strip() or None

    # 1. 驗證愛心數量欄位
    if not heart_amount_str:
        flash("請輸入要轉移的愛心值數量。", "danger")
        return redirect(url_for('user.qr_transfer', token=token))

    try:
        heart_amount = int(heart_amount_str)
        if heart_amount <= 0:
            flash("轉移愛心值數量必須大於 0。", "danger")
            return redirect(url_for('user.qr_transfer', token=token))
    except ValueError:
        flash("愛心值數量必須是整數數字。", "danger")
        return redirect(url_for('user.qr_transfer', token=token))

    try:
        receiver = User.get_by_qr_code_token(token)
        if not receiver:
            abort(404, description="接收者不存在。")

        if receiver.id == sender_id:
            flash("您無法發送愛心給自己！", "warning")
            return redirect(url_for('user.profile'))

        # 2 & 3. 呼叫 Model atomically 進行轉帳
        # transfer_hearts 會驗證 sender 餘額及 receiver 是否存在
        HeartTransaction.transfer_hearts(
            sender_id=sender_id,
            receiver_id=receiver.id,
            amount=heart_amount,
            message=thank_you_message
        )
        flash("成功發送愛心與感謝！人氣值已成功送達給對方。", "success")
        return redirect(url_for('user.profile'))
    except ValueError as e:
        flash(f"轉移失敗：{str(e)}", "danger")
        return redirect(url_for('user.qr_transfer', token=token))
    except Exception as e:
        flash(f"轉移失敗，系統錯誤：{str(e)}", "danger")
        return redirect(url_for('user.qr_transfer', token=token))


@user_bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    愛心與人氣排行榜。
    
    GET:
        - 查詢 users 表中人氣值最高的前 10 名使用者。
        - 渲染 `templates/user/leaderboard.html`。
    """
    try:
        top_users = User.get_top_by_popularity(limit=10)
        return render_template("user/leaderboard.html", top_users=top_users)
    except Exception as e:
        flash(f"載入排行榜失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))
