"""
認證模組 (Auth Route Implementation)
處理註冊、登入與登出邏輯。
"""

import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.db import get_db_connection

# 建立認證 Blueprint
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    註冊新使用者。
    """
    if 'user_id' in session:
        return redirect(url_for('user.profile'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        name = request.form.get("name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        department = request.form.get("department", "").strip()

        # 1. 驗證必填欄位
        if not (username and password and name and student_id):
            flash("請填寫所有必填欄位！", "warning")
            return render_template("auth/register.html")

        # 2. 檢查學號/帳號是否重複
        conn = get_db_connection()
        existing = conn.execute(
            "SELECT username, student_id FROM users WHERE username = ? OR student_id = ?;",
            (username, student_id)
        ).fetchone()
        conn.close()

        if existing:
            if existing['username'] == username:
                flash("該帳號已被註冊！", "danger")
            else:
                flash("該學號已被註冊！", "danger")
            return render_template("auth/register.html")

        # 3. 將密碼雜湊，產生專屬 QR Code Token 並寫入資料庫
        password_hash = generate_password_hash(password)
        qr_code_token = secrets.token_hex(16)

        try:
            User.create(
                username=username,
                password_hash=password_hash,
                name=name,
                student_id=student_id,
                department=department if department else None,
                qr_code_token=qr_code_token
            )
            flash("註冊成功！請登入您的帳戶。", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"註冊時發生錯誤：{str(e)}", "danger")
            return render_template("auth/register.html")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    使用者登入。
    """
    if 'user_id' in session:
        return redirect(url_for('user.profile'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not (username and password):
            flash("請輸入帳號與密碼！", "warning")
            return render_template("auth/login.html")

        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash(f"歡迎回來，{user.name}！", "success")
            return redirect(url_for("user.profile"))
        else:
            flash("帳號或密碼錯誤，請再試一次。", "danger")
            return render_template("auth/login.html")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """
    使用者登出。
    """
    session.clear()
    flash("您已成功登出。", "info")
    return redirect(url_for("auth.login"))
