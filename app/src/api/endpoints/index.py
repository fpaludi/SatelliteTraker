from enum import Enum
from fastapi import APIRouter, Depends, Request
from logger import get_logger
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Global Objects
router = APIRouter()
logger = get_logger(__name__)

templates = Jinja2Templates(directory="templates")


@router.get("/dashboard/{dashboard_id}", response_class=HTMLResponse)
def root(request: Request, dashboard_id):
    return templates.TemplateResponse(
        "home.html", {"request": request, "dashboard_id": dashboard_id}
    )
