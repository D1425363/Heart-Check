"""
使用者與愛心模組 (User & Heart Route Implementation)
處理個人檔案、愛心排行榜、QR Code 掃描、愛心值轉移與徽章管理。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models.user import User, HeartTransaction, Badge

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

    # 4. 生成 QR Code 的 URL
    # 在網頁上會用 JS 將這個 URL 轉換成 QR Code 圖片
    qr_code_url = request.url_root.rstrip('/') + url_for('user.qr_transfer', token=user.qr_code_token)

    return render_template(
        "user/profile.html", 
        user=user, 
        badges=badges, 
        pinned_badges=pinned_badges,
        transactions=transactions,
        qr_code_url=qr_code_url
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

    if heart_amount <= 0:
        flash("發送數量必須大於 0 顆愛心！", "warning")
        return redirect(url_for("user.qr_transfer", token=token))

    sender = User.get_by_id(sender_id)
    if sender.heart_balance < heart_amount:
        flash(f"愛心值餘額不足！您目前僅剩餘 {sender.heart_balance} 顆愛心。", "danger")
        return redirect(url_for("user.qr_transfer", token=token))

    # 執行轉移
    try:
        HeartTransaction.transfer_hearts(sender_id, receiver.id, heart_amount, thank_you_message)
        
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
    top_users = User.get_top_by_popularity(limit=10)
    
    # 載入前十名使用者釘選的徽章
    for user in top_users:
        user.pinned_badges = Badge.get_pinned_by_user_id(user.id)
        
    return render_template("user/leaderboard.html", top_users=top_users)
