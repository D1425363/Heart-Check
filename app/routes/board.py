"""
公告板與校園資訊模組 (Board & Information Route Implementation)
處理首頁大廳、宿舍與校園公告 CRUD、愛心留言牆、校園交通與學餐資訊展示。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models.announcement import Announcement
from app.models.item import Item
from app.models.user import User, HeartTransaction
from app.models.db import get_db_connection
from app.routes.user import login_required

# 建立公告板與資訊 Blueprint
board_bp = Blueprint("board", __name__)


def is_admin(user):
    """
    權限驗證輔助函式：
    如果帳號為 admin、學號以 ADMIN 開頭，或科系/部門包含「幹部」、「管理」、「學生會」等關鍵字，視為管理者/幹部。
    """
    if not user:
        return False
    username_lower = user.username.lower()
    dept = user.department or ""
    std_id = (user.student_id or "").upper()
    return (
        username_lower == "admin" or
        std_id.startswith("ADMIN") or
        any(keyword in dept for keyword in ["幹部", "管理", "學生會", "自治會"])
    )


def admin_required(f):
    """
    自訂的管理者/幹部權限驗證裝飾器。
    """
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("請先登入後再進行此操作！", "warning")
            return redirect(url_for('auth.login'))
        
        user = User.get_by_id(session['user_id'])
        if not is_admin(user):
            flash("權限不足！此操作僅限校園幹部或管理員。", "danger")
            return redirect(url_for('board.announcements'))
        return f(*args, **kwargs)
    return decorated_function


@board_bp.route("/", methods=["GET"])
def home():
    """
    校園互助平台首頁。
    """
    try:
        # 1. 查詢最新 3 筆公告
        all_announcements = Announcement.get_all()
        latest_announcements = all_announcements[:3]

        # 2. 查詢最新 3 筆協尋中 (unclaimed) 的失物招領物件
        all_items = Item.get_all()
        unclaimed_items = [i for i in all_items if i.status == 'unclaimed']
        latest_items = unclaimed_items[:3]

        # 3. 查詢最新 5 筆愛心交易（含匿名）
        all_transactions = HeartTransaction.get_all()
        recent_transactions = all_transactions[:5]

        # 4. 若已登入，讀取目前使用者資訊
        current_user = None
        if 'user_id' in session:
            current_user = User.get_by_id(session['user_id'])

        return render_template(
            "board/home.html",
            announcements=latest_announcements,
            items=latest_items,
            current_user=current_user,
            latest_thanks=recent_transactions,
            recent_transactions=recent_transactions
        )

    except Exception as e:
        # 出現例外時，仍嘗試渲染基本頁面，避免網頁完全掛掉
        flash(f"加載首頁部分資料失敗：{str(e)}", "warning")
        return render_template("board/home.html", announcements=[], items=[], current_user=None, recent_transactions=[])


@board_bp.route("/announcements", methods=["GET"])
def announcements():
    """
    公告清單頁面。
    """
    category = request.args.get("category", "").strip()

    if category in ("dorm", "campus"):
        announcements_list = Announcement.get_by_category(category)
    else:
        announcements_list = Announcement.get_all()

    # 檢查當前使用者是否具備管理員/幹部權限，以便在 UI 顯示「新增公告」按鈕
    user_is_admin = False
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
        user_is_admin = is_admin(user)

    return render_template(
        "board/announcements.html",
        announcements=announcements_list,
        current_category=category,
        user_is_admin=user_is_admin
    )


@board_bp.route("/announcements/new", methods=["GET", "POST"])
@admin_required
def new_announcement():
    """
    建立新公告 (限管理者/幹部)。
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "").strip()

        if not (title and content and category):
            flash("請填寫所有必填欄位！", "warning")
            return render_template("board/announcement_new.html")

        if category not in ("dorm", "campus"):
            flash("公告分類不正確！", "danger")
            return render_template("board/announcement_new.html")

        try:
            Announcement.create(title, content, category, session['user_id'])
            flash("發布公告成功！", "success")
            return redirect(url_for("board.announcements"))
        except Exception as e:
            flash(f"發布公告失敗：{str(e)}", "danger")
            return render_template("board/announcement_new.html")

    return render_template("board/announcement_new.html")


@board_bp.route("/announcements/<int:announcement_id>/edit", methods=["GET"])
@admin_required
def edit_announcement(announcement_id):
    """
    編輯公告頁面 (限該公告作者或管理員)。
    """
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        flash("此公告不存在！", "warning")
        return redirect(url_for("board.announcements"))

    # 僅允許原作者或管理員編輯
    current_user_id = session['user_id']
    user = User.get_by_id(current_user_id)
    
    if announcement.author_id != current_user_id and user.username.lower() != 'admin':
        flash("您沒有修改此公告的權限！", "danger")
        return redirect(url_for("board.announcements"))

    return render_template("board/announcement_edit.html", announcement=announcement)


@board_bp.route("/announcements/<int:announcement_id>/update", methods=["POST"])
@admin_required
def update_announcement(announcement_id):
    """
    更新公告。
    """
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        flash("此公告不存在！", "warning")
        return redirect(url_for("board.announcements"))

    current_user_id = session['user_id']
    user = User.get_by_id(current_user_id)
    
    if announcement.author_id != current_user_id and user.username.lower() != 'admin':
        flash("您沒有修改此公告的權限！", "danger")
        return redirect(url_for("board.announcements"))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "").strip()

    if not (title and content and category):
        flash("請填寫所有必填欄位！", "warning")
        return render_template("board/announcement_edit.html", announcement=announcement)

    if category not in ("dorm", "campus"):
        flash("分類不正確！", "danger")
        return render_template("board/announcement_edit.html", announcement=announcement)

    announcement.title = title
    announcement.content = content
    announcement.category = category

    try:
        announcement.update()
        flash("公告更新成功！", "success")
        return redirect(url_for("board.announcements"))
    except Exception as e:
        flash(f"更新失敗：{str(e)}", "danger")
        return render_template("board/announcement_edit.html", announcement=announcement)


@board_bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
@admin_required
def delete_announcement(announcement_id):
    """
    刪除公告。
    """
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        flash("此公告不存在！", "warning")
        return redirect(url_for("board.announcements"))

    current_user_id = session['user_id']
    user = User.get_by_id(current_user_id)

    if announcement.author_id != current_user_id and user.username.lower() != 'admin':
        flash("您沒有刪除此公告的權限！", "danger")
        return redirect(url_for("board.announcements"))

    try:
        announcement.delete()
        flash("公告已成功刪除。", "success")
    except Exception as e:
        flash(f"刪除失敗：{str(e)}", "danger")

    return redirect(url_for("board.announcements"))


@board_bp.route("/info/traffic", methods=["GET"])
def traffic_info():
    """
    校園交通時刻表。
    """
    return render_template("board/traffic.html")


@board_bp.route("/info/restaurants", methods=["GET"])
def restaurant_info():
    """
    學餐與校園餐廳評價。
    """
    return render_template("board/restaurants.html")
