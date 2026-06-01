"""
失物招領模組 (Lost & Found Route Skeleton)
處理物品發布、列表瀏覽、詳情查看、編輯、刪除與標記尋回狀態。
"""

import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from app.models.item import Item

# 建立失物招領 Blueprint
item_bp = Blueprint("item", __name__)


@item_bp.route("/items", methods=["GET"])
def list_items():
    """
    失物招領列表。
    
    GET:
        - 接收查詢參數：type (lost/found), status (unclaimed/claimed), q (關鍵字)。
        - 查詢 items 表，依建立時間排序。
        - 渲染 `templates/item/list.html`。
    """
    try:
        items = Item.get_all()

        # 接收過濾參數
        item_type = request.args.get("type", "").strip()
        status = request.args.get("status", "").strip()
        q = request.args.get("q", "").strip()

        # 進行 Python 層級過濾
        if item_type in ('lost', 'found'):
            items = [i for i in items if i.item_type == item_type]

        if status in ('unclaimed', 'claimed'):
            items = [i for i in items if i.status == status]

        if q:
            q_lower = q.lower()
            items = [
                i for i in items 
                if q_lower in i.title.lower() or 
                   q_lower in i.description.lower() or 
                   q_lower in i.location.lower()
            ]

        return render_template(
            "item/list.html", 
            items=items, 
            type=item_type, 
            status=status, 
            q=q
        )
    except Exception as e:
        flash(f"載入失物招領清單失敗：{str(e)}", "danger")
        return redirect(url_for('board.home'))


@item_bp.route("/items/new", methods=["GET", "POST"])
def new_item():
    """
    建立新的失物招領公告。
    
    GET:
        - 檢查登入狀態。
        - 渲染 `templates/item/new.html` 表單頁。
    POST:
        - 接收表單欄位：title, description, location, item_type, contact_info。
        - 接收檔案欄位：image。
        - 處理邏輯：
            1. 檢查登入狀態並驗證必填欄位。
            2. 若有圖片則處理上傳並存入 static 目錄。
            3. 將狀態預設為 `unclaimed`。
            4. 寫入 items 表。
            5. 重導向至 `/items`。
        - 錯誤處理：
            - 欄位缺失：重新渲染 `item/new.html` 並顯示錯誤提示「請填寫所有必填欄位」。
    """
    if 'user_id' not in session:
        flash("請先登入後再發布失物招領公告。", "warning")
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        item_type = request.form.get("item_type", "").strip()
        contact_info = request.form.get("contact_info", "").strip() or None

        # 1. 驗證必填欄位
        if not title or not description or not location or item_type not in ('lost', 'found'):
            flash("請填寫所有必填欄位並選擇正確的類型（尋物/拾獲）。", "danger")
            return render_template(
                "item/new.html", 
                title=title, 
                description=description, 
                location=location, 
                item_type=item_type, 
                contact_info=contact_info
            )

        # 2. 處理圖片上傳
        image_url = None
        try:
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    # 確保上傳目錄存在
                    upload_folder = os.path.join('app', 'static', 'images')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # 重新命名防衝突
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext not in ('.png', '.jpg', '.jpeg', '.gif'):
                        flash("不支援的檔案格式，請上傳 PNG、JPG、JPEG 或 GIF 圖片。", "danger")
                        return render_template(
                            "item/new.html", 
                            title=title, 
                            description=description, 
                            location=location, 
                            item_type=item_type, 
                            contact_info=contact_info
                        )
                        
                    filename = f"{uuid.uuid4().hex}{ext}"
                    file.save(os.path.join(upload_folder, filename))
                    image_url = f"images/{filename}"
        except Exception as e:
            flash(f"圖片上傳失敗：{str(e)}", "danger")
            return render_template(
                "item/new.html", 
                title=title, 
                description=description, 
                location=location, 
                item_type=item_type, 
                contact_info=contact_info
            )

        # 3 & 4. 寫入 items 表
        try:
            Item.create(
                title=title,
                description=description,
                location=location,
                item_type=item_type,
                status='unclaimed',
                user_id=session['user_id'],
                image_url=image_url,
                contact_info=contact_info
            )
            flash("公告發布成功！", "success")
            return redirect(url_for('item.list_items'))
        except Exception as e:
            # 若寫入失敗且已存圖片，進行清理
            if image_url:
                try:
                    os.remove(os.path.join('app', 'static', image_url))
                except Exception:
                    pass
            flash(f"發布失敗：{str(e)}", "danger")
            return render_template(
                "item/new.html", 
                title=title, 
                description=description, 
                location=location, 
                item_type=item_type, 
                contact_info=contact_info
            )

    return render_template("item/new.html")


@item_bp.route("/items/<int:item_id>", methods=["GET"])
def item_detail(item_id):
    """
    失物招領詳細頁面。
    
    GET:
        - 根據 item_id 查詢物品詳細資料。
        - 若無此物品，回傳 404。
        - 渲染 `templates/item/detail.html`。
    """
    try:
        item = Item.get_by_id(item_id)
        if not item:
            abort(404, description="此物品公告不存在或已被刪除。")
        return render_template("item/detail.html", item=item)
    except Exception as e:
        if hasattr(e, 'code') and e.code == 404:
            raise e
        flash(f"載入物品詳情失敗：{str(e)}", "danger")
        return redirect(url_for('item.list_items'))


@item_bp.route("/items/<int:item_id>/edit", methods=["GET"])
def edit_item(item_id):
    """
    編輯失物招領頁面。
    
    GET:
        - 檢查登入狀態與編輯權限（限發布者或管理員）。
        - 查詢物品資料，帶入現有內容。
        - 渲染 `templates/item/edit.html`。
    """
    if 'user_id' not in session:
        flash("請先登入後再進行編輯。", "warning")
        return redirect(url_for('auth.login'))

    try:
        item = Item.get_by_id(item_id)
        if not item:
            abort(404, description="此物品公告不存在。")

        if item.user_id != session['user_id']:
            flash("您沒有權限編輯此公告。", "danger")
            return redirect(url_for('item.item_detail', item_id=item_id))

        return render_template("item/edit.html", item=item)
    except Exception as e:
        if hasattr(e, 'code') and e.code == 404:
            raise e
        flash(f"載入編輯頁面失敗：{str(e)}", "danger")
        return redirect(url_for('item.list_items'))


@item_bp.route("/items/<int:item_id>/update", methods=["POST"])
def update_item(item_id):
    """
    更新失物招領公告。
    
    POST:
        - 檢查登入狀態與編輯權限。
        - 接收表單欄位：title, description, location, item_type, contact_info, status。
        - 接收檔案欄位：image (若有上傳新圖則覆蓋)。
        - 更新 items 資料庫，並重導向至 `/items/<item_id>`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        item = Item.get_by_id(item_id)
        if not item:
            abort(404, description="物品公告不存在。")

        if item.user_id != session['user_id']:
            flash("您沒有權限修改此公告。", "danger")
            return redirect(url_for('item.item_detail', item_id=item_id))

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        item_type = request.form.get("item_type", "").strip()
        status = request.form.get("status", "").strip()
        contact_info = request.form.get("contact_info", "").strip() or None

        # 驗證必填欄位
        if not title or not description or not location or item_type not in ('lost', 'found') or status not in ('unclaimed', 'claimed'):
            flash("請填寫所有必填欄位，並選擇正確的類型與狀態。", "danger")
            return render_template("item/edit.html", item=item)

        # 處理新圖片上傳
        image_url = item.image_url
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_folder = os.path.join('app', 'static', 'images')
                os.makedirs(upload_folder, exist_ok=True)
                
                ext = os.path.splitext(file.filename)[1].lower()
                if ext not in ('.png', '.jpg', '.jpeg', '.gif'):
                    flash("不支援的檔案格式，請上傳 PNG、JPG、JPEG 或 GIF 圖片。", "danger")
                    return render_template("item/edit.html", item=item)

                filename = f"{uuid.uuid4().hex}{ext}"
                file.save(os.path.join(upload_folder, filename))
                
                # 刪除舊圖片檔案
                if item.image_url:
                    old_path = os.path.join('app', 'static', item.image_url)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                image_url = f"images/{filename}"

        # 更新 Model 屬性並寫入資料庫
        item.title = title
        item.description = description
        item.location = location
        item.item_type = item_type
        item.status = status
        item.contact_info = contact_info
        item.image_url = image_url

        item.update()
        flash("公告更新成功！", "success")
        return redirect(url_for('item.item_detail', item_id=item_id))
    except Exception as e:
        flash(f"更新失敗：{str(e)}", "danger")
        return redirect(url_for('item.list_items'))


@item_bp.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    """
    刪除失物招領公告。
    
    POST:
        - 檢查登入狀態與編輯權限。
        - 自 items 資料庫刪除該物品。
        - 刪除對應的實體圖片檔案。
        - 重導向至 `/items`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        item = Item.get_by_id(item_id)
        if not item:
            abort(404, description="物品公告不存在。")

        if item.user_id != session['user_id']:
            flash("您沒有權限刪除此公告。", "danger")
            return redirect(url_for('item.item_detail', item_id=item_id))

        # 刪除實體圖片檔案
        if item.image_url:
            img_path = os.path.join('app', 'static', item.image_url)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass

        item.delete()
        flash("公告已成功刪除。", "success")
        return redirect(url_for('item.list_items'))
    except Exception as e:
        flash(f"刪除失敗：{str(e)}", "danger")
        return redirect(url_for('item.list_items'))


@item_bp.route("/items/<int:item_id>/claim", methods=["POST"])
def claim_item(item_id):
    """
    標記失物招領物品為已認領/已尋回。
    
    POST:
        - 檢查登入狀態與編輯權限。
        - 將 items 表中的物品 status 設為 `claimed`。
        - 重導向至 `/items/<item_id>`。
    """
    if 'user_id' not in session:
        flash("請先登入。", "warning")
        return redirect(url_for('auth.login'))

    try:
        item = Item.get_by_id(item_id)
        if not item:
            abort(404, description="物品公告不存在。")

        if item.user_id != session['user_id']:
            flash("您沒有權限變更此公告狀態。", "danger")
            return redirect(url_for('item.item_detail', item_id=item_id))

        item.status = 'claimed'
        item.update()
        flash("物品狀態已更新為已認領/已尋回！", "success")
        return redirect(url_for('item.item_detail', item_id=item_id))
    except Exception as e:
        flash(f"變更狀態失敗：{str(e)}", "danger")
        return redirect(url_for('item.item_detail', item_id=item_id))
