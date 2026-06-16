"""
校園求助區 (Campus Help) Route Implementation
提供找筆記、找組員、找失物、找課本、問課程等五大分類的求助發布與瀏覽功能。
"""

import functools
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models.help import HelpRequest, CATEGORY_META, VALID_CATEGORIES

help_bp = Blueprint("help", __name__, url_prefix="/help")


def login_required(f):
    """自訂登入驗證裝飾器。"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("請先登入後再進行此操作！", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@help_bp.route("/", methods=["GET"])
def index():
    """
    校園求助區首頁：顯示五大分類卡片，
    以及每個分類目前開放中的需求數量。
    """
    category_stats = {}
    for key in VALID_CATEGORIES:
        requests = HelpRequest.get_all(category=key, status='open')
        category_stats[key] = {
            **CATEGORY_META[key],
            'count': len(requests),
            'key': key,
        }
    return render_template("help/index.html", category_stats=category_stats)


@help_bp.route("/<category>", methods=["GET"])
def list_requests(category):
    """
    顯示特定分類下所有開放中的求助。
    """
    if category not in VALID_CATEGORIES:
        flash("無效的分類！", "danger")
        return redirect(url_for("help.index"))

    status_filter = request.args.get("status", "open")
    requests = HelpRequest.get_all(category=category, status=status_filter if status_filter in ('open', 'resolved') else 'open')
    meta = CATEGORY_META[category]

    return render_template(
        "help/list.html",
        requests=requests,
        category=category,
        meta=meta,
        status_filter=status_filter,
    )


@help_bp.route("/<category>/new", methods=["GET", "POST"])
@login_required
def new_request(category):
    """
    新增求助需求表單 (GET) 及處理送出 (POST)。
    """
    if category not in VALID_CATEGORIES:
        flash("無效的分類！", "danger")
        return redirect(url_for("help.index"))

    meta = CATEGORY_META[category]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not description:
            flash("標題與詳細說明均為必填欄位！", "danger")
            return render_template("help/new.html", category=category, meta=meta,
                                   form_title=title, form_description=description)

        if len(title) > 100:
            flash("標題不能超過 100 個字！", "warning")
            return render_template("help/new.html", category=category, meta=meta,
                                   form_title=title, form_description=description)

        try:
            HelpRequest.create(
                user_id=session['user_id'],
                category=category,
                title=title,
                description=description,
            )
            flash(f"求助發布成功！{meta['icon']} 希望很快有同學幫到你。", "success")
            return redirect(url_for("help.list_requests", category=category))
        except Exception as e:
            flash(f"發布失敗，請稍後再試：{str(e)}", "danger")
            return render_template("help/new.html", category=category, meta=meta,
                                   form_title=title, form_description=description)

    return render_template("help/new.html", category=category, meta=meta,
                           form_title="", form_description="")


@help_bp.route("/<category>/<int:request_id>/resolve", methods=["POST"])
@login_required
def resolve_request(category, request_id):
    """
    將求助標記為已解決（只有發布者本人才能操作）。
    """
    help_req = HelpRequest.get_by_id(request_id)
    if not help_req:
        flash("找不到此求助紀錄！", "danger")
        return redirect(url_for("help.list_requests", category=category))

    if help_req.user_id != session['user_id']:
        flash("您沒有權限修改此求助！", "warning")
        return redirect(url_for("help.list_requests", category=category))

    try:
        help_req.mark_resolved()
        flash("已標記為問題已解決！感謝熱心的同學幫助你 💖", "success")
    except Exception as e:
        flash(f"操作失敗：{str(e)}", "danger")

    return redirect(url_for("help.list_requests", category=category))


@help_bp.route("/<category>/<int:request_id>/delete", methods=["POST"])
@login_required
def delete_request(category, request_id):
    """
    刪除求助紀錄（只有發布者本人才能操作）。
    """
    help_req = HelpRequest.get_by_id(request_id)
    if not help_req:
        flash("找不到此求助紀錄！", "danger")
        return redirect(url_for("help.list_requests", category=category))

    if help_req.user_id != session['user_id']:
        flash("您沒有權限刪除此求助！", "warning")
        return redirect(url_for("help.list_requests", category=category))

    try:
        help_req.delete()
        flash("求助紀錄已刪除。", "success")
    except Exception as e:
        flash(f"刪除失敗：{str(e)}", "danger")

    return redirect(url_for("help.list_requests", category=category))
