"""
認證模組 (Auth Route Skeleton)
處理註冊、登入與登出邏輯。
"""

import sqlite3
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User

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
    # 若使用者已登入，直接重導向至個人檔案頁面
    if 'user_id' in session:
        return redirect(url_for('user.profile'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        name = request.form.get("name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        department = request.form.get("department", "").strip() or None

        # 1. 驗證必填欄位
        if not username or not password or not name or not student_id:
            flash("請填寫所有必填欄位（帳號、密碼、姓名、學號）。", "danger")
            return render_template("auth/register.html", username=username, name=name, student_id=student_id, department=department)

        # 2. 檢查帳號是否已被註冊 (主動檢查)
        try:
            if User.get_by_username(username):
                flash("該帳號已被註冊，請換一個帳號。", "danger")
                return render_template("auth/register.html", username=username, name=name, student_id=student_id, department=department)
        except Exception as e:
            flash("系統錯誤，請稍後再試。", "danger")
            return render_template("auth/register.html", username=username, name=name, student_id=student_id, department=department)

        # 3 & 4. 雜湊密碼並儲存
        try:
            password_hash = generate_password_hash(password)
            User.create(
                username=username,
                password_hash=password_hash,
                name=name,
                student_id=student_id,
                department=department
            )
            flash("註冊成功，請登入！", "success")
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError as e:
            err_msg = str(e).lower()
            if "username" in err_msg:
                flash("該帳號已被註冊，請換一個帳號。", "danger")
            elif "student_id" in err_msg:
                flash("該學號已被註冊，請檢查學號是否正確。", "danger")
            else:
                flash("註冊失敗，帳號或學號重複。", "danger")
            return render_template("auth/register.html", username=username, name=name, student_id=student_id, department=department)
        except Exception as e:
            flash(f"註冊失敗：{str(e)}", "danger")
            return render_template("auth/register.html", username=username, name=name, student_id=student_id, department=department)

    return render_template("auth/register.html")


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
    # 若使用者已登入，直接重導向至個人檔案頁面
    if 'user_id' in session:
        return redirect(url_for('user.profile'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # 驗證必填欄位
        if not username or not password:
            flash("請填寫帳號與密碼。", "danger")
            return render_template("auth/login.html", username=username)

        try:
            user = User.get_by_username(username)
            # 比對帳密
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash(f"歡迎回來，{user.name}！", "success")
                return redirect(url_for('user.profile'))
            else:
                flash("帳號或密碼錯誤。", "danger")
                return render_template("auth/login.html", username=username)
        except Exception as e:
            flash(f"登入失敗：{str(e)}", "danger")
            return render_template("auth/login.html", username=username)

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """
    使用者登出。
    
    GET:
        - 清除 session。
        - 重導向至登入頁面 `/login`。
    """
    session.clear()
    flash("您已成功登出。", "info")
    return redirect(url_for('auth.login'))
