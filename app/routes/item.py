"""
失物招領與留言模組 (Lost & Found Route Implementation)
處理物品發布、列表瀏覽、詳情查看、編輯、刪除、標記尋回，以及留言互動。
"""

import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from werkzeug.utils import secure_filename
from app.models.item import Item
from app.models.comment import Comment
from app.models.user import User, Badge
from app.models.db import get_db_connection
from app.routes.user import login_required

# 建立失物招領 Blueprint
item_bp = Blueprint("item", __name__)


def allowed_file(filename):
    """
    檢查檔案副檔名是否為圖片。
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@item_bp.route("/items", methods=["GET"])
def list_items():
    """
    失物招領列表，支援條件過濾與搜尋。
    """
    item_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()

    query = """
        SELECT i.*, u.name AS user_name
        FROM items i
        JOIN users u ON i.user_id = u.id
        WHERE 1=1
    """
    params = []

    if item_type in ("lost", "found"):
        query += " AND i.item_type = ?"
        params.append(item_type)

    if status in ("unclaimed", "claimed"):
        query += " AND i.status = ?"
        params.append(status)

    if q:
        query += " AND (i.title LIKE ? OR i.description LIKE ? OR i.location LIKE ?)"
        like_pattern = f"%{q}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    query += " ORDER BY i.created_at DESC"

    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    items = [Item.from_row(row) for row in rows]

    return render_template(
        "item/list.html",
        items=items,
        current_type=item_type,
        current_status=status,
        current_q=q
    )


@item_bp.route("/items/new", methods=["GET", "POST"])
@login_required
def new_item():
    """
    建立新的失物招領公告。
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        item_type = request.form.get("item_type", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        image_file = request.files.get("image")

        # 1. 驗證必填欄位
        if not (title and description and location and item_type):
            flash("請填寫所有必填欄位！", "warning")
            return render_template("item/new.html")

        if item_type not in ("lost", "found"):
            flash("物品類型不正確！", "danger")
            return render_template("item/new.html")

        # 2. 處理圖片上傳
        image_url = None
        if image_file and image_file.filename != '':
            if allowed_file(image_file.filename):
                filename = secrets.token_hex(8) + "_" + secure_filename(image_file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(upload_path)
                image_url = "uploads/" + filename
            else:
                flash("不支援的檔案格式！僅允許 PNG, JPG, JPEG, GIF, WEBP 圖片格式。", "warning")
                return render_template("item/new.html")

        # 3. 寫入資料庫
        try:
            Item.create(
                title=title,
                description=description,
                location=location,
                item_type=item_type,
                status="unclaimed",
                user_id=session['user_id'],
                image_url=image_url,
                contact_info=contact_info if contact_info else None
            )
            
            # 檢查並頒發「校園情報員」徽章
            Badge.check_and_award(session['user_id'])
            
            flash("發布失物招領公告成功！", "success")
            return redirect(url_for("item.list_items"))
        except Exception as e:
            flash(f"發布公告失敗：{str(e)}", "danger")
            return render_template("item/new.html")

    return render_template("item/new.html")


@item_bp.route("/items/<int:item_id>", methods=["GET"])
def item_detail(item_id):
    """
    失物招領詳細頁面與留言板。
    """
    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在或已被刪除！", "warning")
        return redirect(url_for("item.list_items"))

    comments = Comment.get_by_item_id(item_id)
    
    # 查詢發布者釘選的徽章展示
    owner = User.get_by_id(item.user_id)
    owner_pinned_badges = Badge.get_pinned_by_user_id(owner.id) if owner else []

    return render_template(
        "item/detail.html",
        item=item,
        comments=comments,
        owner_pinned_badges=owner_pinned_badges
    )


@item_bp.route("/items/<int:item_id>/edit", methods=["GET"])
@login_required
def edit_item(item_id):
    """
    編輯失物招領頁面。
    """
    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    if item.user_id != session['user_id']:
        flash("您沒有修改此公告的權限！", "danger")
        return redirect(url_for("item.item_detail", item_id=item_id))

    return render_template("item/edit.html", item=item)


@item_bp.route("/items/<int:item_id>/update", methods=["POST"])
@login_required
def update_item(item_id):
    """
    更新失物招領公告。
    """
    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    if item.user_id != session['user_id']:
        flash("您沒有修改此公告的權限！", "danger")
        return redirect(url_for("item.item_detail", item_id=item_id))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    location = request.form.get("location", "").strip()
    item_type = request.form.get("item_type", "").strip()
    status = request.form.get("status", "").strip()
    contact_info = request.form.get("contact_info", "").strip()
    image_file = request.files.get("image")

    if not (title and description and location and item_type and status):
        flash("請填寫所有必填欄位！", "warning")
        return render_template("item/edit.html", item=item)

    if item_type not in ("lost", "found") or status not in ("unclaimed", "claimed"):
        flash("參數格式不正確！", "danger")
        return render_template("item/edit.html", item=item)

    # 處理圖片更新
    if image_file and image_file.filename != '':
        if allowed_file(image_file.filename):
            # 刪除舊圖片 (如果存在)
            if item.image_url:
                old_img_path = os.path.join(current_app.root_path, "static", item.image_url)
                if os.path.exists(old_img_path):
                    try:
                        os.remove(old_img_path)
                    except OSError:
                        pass
            
            # 保存新圖片
            filename = secrets.token_hex(8) + "_" + secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(upload_path)
            item.image_url = "uploads/" + filename
        else:
            flash("不支援的檔案格式！", "warning")
            return render_template("item/edit.html", item=item)

    item.title = title
    item.description = description
    item.location = location
    item.item_type = item_type
    
    # 如果狀態變為 claimed 且之前不是 claimed，可以檢查徽章
    old_status = item.status
    item.status = status
    item.contact_info = contact_info if contact_info else None

    try:
        item.update()
        
        # 狀態改變為 claimed 可檢查「尋物達人」徽章
        if old_status != "claimed" and status == "claimed":
            Badge.check_and_award(session['user_id'])

        flash("更新公告成功！", "success")
        return redirect(url_for("item.item_detail", item_id=item.id))
    except Exception as e:
        flash(f"更新公告失敗：{str(e)}", "danger")
        return render_template("item/edit.html", item=item)


@item_bp.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    """
    刪除失物招領公告。
    """
    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    if item.user_id != session['user_id']:
        flash("您沒有刪除此公告的權限！", "danger")
        return redirect(url_for("item.item_detail", item_id=item_id))

    # 刪除實體圖片
    if item.image_url:
        img_path = os.path.join(current_app.root_path, "static", item.image_url)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass

    try:
        item.delete()
        flash("公告已成功刪除。", "success")
    except Exception as e:
        flash(f"刪除失敗：{str(e)}", "danger")

    return redirect(url_for("item.list_items"))


@item_bp.route("/items/<int:item_id>/claim", methods=["POST"])
@login_required
def claim_item(item_id):
    """
    將物品標記為已尋回/已認領。
    """
    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    if item.user_id != session['user_id']:
        flash("您沒有修改此公告的權限！", "danger")
        return redirect(url_for("item.item_detail", item_id=item_id))

    item.status = "claimed"
    try:
        item.update()
        
        # 檢查並頒發「尋物達人」徽章
        Badge.check_and_award(session['user_id'])
        
        flash("物品已成功標記為已認領/已尋回！", "success")
    except Exception as e:
        flash(f"標記失敗：{str(e)}", "danger")

    return redirect(url_for("item.item_detail", item_id=item_id))


# --- 留言板處理 API ---

@item_bp.route("/items/<int:item_id>/comments", methods=["POST"])
@login_required
def add_comment(item_id):
    """
    新增失物招領留言。
    """
    content = request.form.get("content", "").strip()
    if not content:
        flash("留言內容不能為空！", "warning")
        return redirect(url_for("item.item_detail", item_id=item_id))

    item = Item.get_by_id(item_id)
    if not item:
        flash("此物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    try:
        Comment.create(item_id, session['user_id'], content)
        flash("留言發布成功！", "success")
    except Exception as e:
        flash(f"留言失敗：{str(e)}", "danger")

    return redirect(url_for("item.item_detail", item_id=item_id))


@item_bp.route("/items/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    """
    刪除留言 (限留言作者或物品發布者)。
    """
    comment = Comment.get_by_id(comment_id)
    if not comment:
        flash("留言不存在！", "warning")
        return redirect(url_for("item.list_items"))

    item = Item.get_by_id(comment.item_id)
    if not item:
        flash("物品公告不存在！", "warning")
        return redirect(url_for("item.list_items"))

    # 僅允許留言作者或該失物招領的發布者刪除留言
    if comment.user_id == session['user_id'] or item.user_id == session['user_id']:
        try:
            Comment.delete(comment_id)
            flash("留言已刪除。", "success")
        except Exception as e:
            flash(f"刪除留言失敗：{str(e)}", "danger")
    else:
        flash("您沒有權限刪除此留言！", "danger")

    return redirect(url_for("item.item_detail", item_id=comment.item_id))
