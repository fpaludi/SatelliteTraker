from fastapi import FastAPI
from settings import settings  # noqa
from logger import configure_logger
from fastapi.staticfiles import StaticFiles


def app_factory():
    configure_logger()
    app = FastAPI(title="BooksAPI",)
    from src.api.api import api_router

    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app
