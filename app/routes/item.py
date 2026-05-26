"""
失物招領模組 (Lost & Found Route Skeleton)
處理物品發布、列表瀏覽、詳情查看、編輯、刪除與標記尋回狀態。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session

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
    pass


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
    """
    pass


@item_bp.route("/items/<int:item_id>", methods=["GET"])
def item_detail(item_id):
    """
    失物招領詳細頁面。
    
    GET:
        - 根據 item_id 查詢物品詳細資料。
        - 若無此物品，回傳 404。
        - 渲染 `templates/item/detail.html`。
    """
    pass


@item_bp.route("/items/<int:item_id>/edit", methods=["GET"])
def edit_item(item_id):
    """
    編輯失物招領頁面。
    
    GET:
        - 檢查登入狀態與編輯權限（限發布者或管理員）。
        - 查詢物品資料，帶入現有內容。
        - 渲染 `templates/item/edit.html`。
    """
    pass


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
    pass


@item_bp.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    """
    刪除失物招領公告。
    
    POST:
        - 檢查登入狀態與編輯權限。
        - 從 items 資料庫刪除該物品。
        - 刪除對應的實體圖片檔案。
        - 重導向至 `/items`。
    """
    pass


@item_bp.route("/items/<int:item_id>/claim", methods=["POST"])
def claim_item(item_id):
    """
    標記失物招領物品為已認領/已尋回。
    
    POST:
        - 檢查登入狀態與編輯權限。
        - 將 items 表中的物品 status 設為 `claimed`。
        - 重導向至 `/items/<item_id>`。
    """
    pass
