from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def configure_cors(app):
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
