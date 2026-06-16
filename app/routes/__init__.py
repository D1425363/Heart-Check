"""
Routes 模組初始化檔案。
此檔案匯出所有功能模組的 Flask Blueprint，以便在 app 核心中進行註冊。
"""

from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.item import item_bp
from app.routes.board import board_bp
from app.routes.help import help_bp

__all__ = ["auth_bp", "user_bp", "item_bp", "board_bp", "help_bp"]
