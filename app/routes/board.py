"""
公告板與校園資訊模組 (Board & Information Route Skeleton)
處理平台首頁、宿舍/校園公告的 CRUD，以及交通、餐廳資訊等靜態/動態內容展示。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session

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
    pass


@board_bp.route("/announcements", methods=["GET"])
def announcements():
    """
    公告清單頁面。
    
    GET:
        - 接收查詢參數：category (dorm/campus) 進行篩選。
        - 查詢 announcements 表，依發布時間降冪排序。
        - 渲染 `templates/board/announcements.html`。
    """
    pass


@board_bp.route("/announcements/new", methods=["GET", "POST"])
def new_announcement():
    """
    建立新公告 (限管理者/幹部)。
    
    GET:
        - 檢查登入狀態與管理者權限。
        - 渲染 `templates/board/announcement_new.html` 表單頁。
    POST:
        - 接收表單欄位：title, content, category。
        - 處理邏輯：
            1. 檢查登入狀態與管理者權限，驗證必填欄位。
            2. 寫入 announcements 表，author_id 設為目前登入者 ID。
            3. 重導向至 `/announcements`。
    """
    pass


@board_bp.route("/announcements/<int:announcement_id>/edit", methods=["GET"])
def edit_announcement(announcement_id):
    """
    編輯公告頁面 (限該公告作者或高級管理員)。
    
    GET:
        - 檢查登入狀態與權限。
        - 查詢該公告現有資料。
        - 渲染 `templates/board/announcement_edit.html`。
    """
    pass


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
    pass


@board_bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
def delete_announcement(announcement_id):
    """
    刪除公告。
    
    POST:
        - 檢查登入狀態與刪除權限。
        - 自 announcements 資料庫刪除該筆公告。
        - 重導向至 `/announcements`。
    """
    pass


@board_bp.route("/info/traffic", methods=["GET"])
def traffic_info():
    """
    校園交通時刻表。
    
    GET:
        - 載入校車時刻、捷運動態等交通資訊。
        - 渲染 `templates/board/traffic.html`。
    """
    pass


@board_bp.route("/info/restaurants", methods=["GET"])
def restaurant_info():
    """
    學餐與校園餐廳評價。
    
    GET:
        - 載入校園餐廳列表與基本評價資料。
        - 渲染 `templates/board/restaurants.html`。
    """
    pass
