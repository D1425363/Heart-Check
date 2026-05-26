"""
認證模組 (Auth Route Skeleton)
處理註冊、登入與登出邏輯。
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session

# 建立認證 Blueprint
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    註冊新使用者。
    
    GET:
        - 渲染註冊表單 `templates/auth/register.html`。
    POST:
        - 接收表單欄位：username, password, name, student_id, department。
        - 處理邏輯：
            1. 驗證必填欄位。
            2. 檢查學號/帳號是否重複。
            3. 將密碼雜湊，產生專屬 QR Code Token。
            4. 存入 SQLite 資料庫 (users 表)。
            5. 重導向至登入頁面 `/login`。
        - 錯誤處理：
            - 欄位缺失或重複：重新渲染註冊表單並顯示錯誤訊息。
    """
    pass


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    使用者登入。
    
    GET:
        - 渲染登入表單 `templates/auth/login.html`。
    POST:
        - 接收表單欄位：username, password。
        - 處理邏輯：
            1. 比對 username 與資料庫記錄。
            2. 比對 password 與 password_hash。
            3. 成功後將 user_id 寫入 session。
            4. 重導向至個人檔案頁面 `/profile`。
        - 錯誤處理：
            - 帳密錯誤：重新渲染登入表單並顯示錯誤訊息。
    """
    pass


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """
    使用者登出。
    
    GET:
        - 清除 session。
        - 重導向至登入頁面 `/login`。
    """
    pass
