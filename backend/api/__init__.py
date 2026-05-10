"""
API routes: health, chat, upload.
All routers are mounted on the FastAPI app in main.py.
"""

from api.health import router as health_router
from api.chat import router as chat_router
from api.upload import router as upload_router

__all__ = ["health_router", "chat_router", "upload_router"]
