from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import config

router = APIRouter()

@router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = config.base_folder + '/../static/img/favicon.ico'
    return FileResponse(favicon_path)
