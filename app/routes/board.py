"""
公告板與校園資訊模組 (Board & Information Route Skeleton)
處理平台首頁、宿舍/校園公告的 CRUD，以及交通、餐廳資訊等靜態/動態內容展示。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from app.models.announcement import Announcement
from app.models.item import Item
from app.models.user import User

# 建立公告板與資訊 Blueprint
board_bp = Blueprint("board", __name__)


@board_bp.route("/", methods=["GET"])
def home():
    """
    校園互助平台首頁。
    
    GET:
        - 查詢最新的 3 筆公告與最新的 3 筆協尋中失物招領。
        - 載入目前使用者的簡要資訊（若已登入）。
        - 渲染 `templates/board/home.html`。
    """
    try:
        # 1. 查詢最新 3 筆公告
        all_announcements = Announcement.get_all()
        latest_announcements = all_announcements[:3]

        # 2. 查詢最新 3 筆協尋中 (unclaimed) 的失物招領物件
        all_items = Item.get_all()
        unclaimed_items = [i for i in all_items if i.status == 'unclaimed']
        latest_items = unclaimed_items[:3]

        # 3. 若已登入，讀取目前使用者資訊
        current_user = None
        if 'user_id' in session:
            current_user = User.get_by_id(session['user_id'])

        return render_template(
            "board/home.html",
            announcements=latest_announcements,
            items=latest_items,
            current_user=current_user
        )
    except Exception as e:
        # 出現例外時，仍嘗試渲染基本頁面，避免網頁完全掛掉
        flash(f"加載首頁部分資料失敗：{str(e)}", "warning")
        return render_template("board/home.html", announcements=[], items=[], current_user=None)


@board_bp.route("/announcements", methods=["GET"])
def announcements():
    """
    公告清單頁面。
    
    GET:
        - 接收查詢參數：category (dorm/campus) 進行篩選。
        - 查詢 announcements 表，依發布時間降冪排序。
        - 渲染 `templates/board/announcements.html`。
    """
    category = request.args.get("category", "").strip()
    try:
        if category in ('dorm', 'campus'):
            announcement_list = Announcement.get_by_category(category)
        else:
            announcement_list = Announcement.get_all()

        return render_template(
            "board/announcements.html",
            announcements=announcement_list,
            category=category
        )
    except Exception as e:
        flash(f"載入公告清單失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))


@board_bp.route("/announcements/new", methods=["GET", "POST"])
def new_announcement():
    """
    建立新公告 (限登入者)。
    
    GET:
        - 檢查登入狀態與權限。
        - 渲染 `templates/board/announcement_new.html` 表單頁。
    POST:
        - 接收表單欄位：title, content, category。
        - 處理邏輯：
            1. 檢查登入狀態與驗證必填欄位。
            2. 寫入 announcements 表，author_id 設為目前登入者 ID。
            3. 重導向至 `/announcements`。
    """
    if 'user_id' not in session:
        flash("請先登入後再發布公告。", "warning")
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "").strip()

        # 1. 驗證欄位是否填寫完整
        if not title or not content or category not in ('dorm', 'campus'):
            flash("請填寫所有必填欄位，並選擇正確的公告分類（宿舍/校園）。", "danger")
            return render_template(
                "board/announcement_new.html",
                title=title,
                content=content,
                category=category
            )

        # 2. 寫入資料庫
        try:
            Announcement.create(
                title=title,
                content=content,
                category=category,
                author_id=session['user_id']
            )
            flash("公告發布成功！", "success")
            return redirect(url_for('board.announcements'))
        except Exception as e:
            flash(f"發布公告失敗：{str(e)}", "danger")
            return render_template(
                "board/announcement_new.html",
                title=title,
                content=content,
                category=category
            )

    return render_template("board/announcement_new.html")


@board_bp.route("/announcements/<int:announcement_id>/edit", methods=["GET"])
def edit_announcement(announcement_id):
    """
    編輯公告頁面 (限該公告作者)。
    
    GET:
        - 檢查登入狀態與權限。
        - 查詢該公告現有資料。
        - 渲染 `templates/board/announcement_edit.html`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        announcement = Announcement.get_by_id(announcement_id)
        if not announcement:
            abort(404, description="該公告不存在或已被刪除。")

        if announcement.author_id != session['user_id']:
            flash("您沒有編輯此公告的權限。", "danger")
            return redirect(url_for('board.announcements'))

        return render_template("board/announcement_edit.html", announcement=announcement)
    except Exception as e:
        if hasattr(e, 'code') and e.code == 404:
            raise e
        flash(f"載入編輯公告失敗：{str(e)}", "danger")
        return redirect(url_for('board.announcements'))


@board_bp.route("/announcements/<int:announcement_id>/update", methods=["POST"])
def update_announcement(announcement_id):
    """
    更新公告。
    
    POST:
        - 檢查登入狀態與修改權限。
        - 接收表單欄位：title, content, category。
        - 更新 announcements 資料庫中對應 id 的欄位與 updated_at。
        - 重導向至 `/announcements`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        announcement = Announcement.get_by_id(announcement_id)
        if not announcement:
            abort(404, description="該公告不存在。")

        if announcement.author_id != session['user_id']:
            flash("您沒有修改此公告的權限。", "danger")
            return redirect(url_for('board.announcements'))

        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "").strip()

        # 驗證欄位
        if not title or not content or category not in ('dorm', 'campus'):
            flash("請填寫所有欄位並選擇正確的公告分類。", "danger")
            return render_template("board/announcement_edit.html", announcement=announcement)

        # 更新
        announcement.title = title
        announcement.content = content
        announcement.category = category
        announcement.update()

        flash("公告更新成功！", "success")
        return redirect(url_for('board.announcements'))
    except Exception as e:
        flash(f"更新公告失敗：{str(e)}", "danger")
        return redirect(url_for('board.announcements'))


@board_bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
def delete_announcement(announcement_id):
    """
    刪除公告。
    
    POST:
        - 檢查登入狀態與刪除權限。
        - 自 announcements 資料庫刪除該筆公告。
        - 重導向至 `/announcements`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        announcement = Announcement.get_by_id(announcement_id)
        if not announcement:
            abort(404, description="該公告不存在。")

        if announcement.author_id != session['user_id']:
            flash("您沒有刪除此公告的權限。", "danger")
            return redirect(url_for('board.announcements'))

        announcement.delete()
        flash("公告已成功刪除。", "success")
        return redirect(url_for('board.announcements'))
    except Exception as e:
        flash(f"刪除公告失敗：{str(e)}", "danger")
        return redirect(url_for('board.announcements'))


@board_bp.route("/info/traffic", methods=["GET"])
def traffic_info():
    """
    校園交通時刻表。
    
    GET:
        - 載入校車時刻、捷運動態等交通資訊。
        - 渲染 `templates/board/traffic.html`。
    """
    return render_template("board/traffic.html")


@board_bp.route("/info/restaurants", methods=["GET"])
def restaurant_info():
    """
    學餐與校園餐廳評價。
    
    GET:
        - 載入校園餐廳列表與基本評價資料。
        - 渲染 `templates/board/restaurants.html`。
    """
    return render_template("board/restaurants.html")
