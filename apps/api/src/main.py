from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.leads import router as leads_router
from src.api.routes.messages import router as messages_router
from src.core.config import get_settings
from src.core.db import Base, engine
from src.schemas import models  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(health_router)
app.include_router(leads_router)
app.include_router(messages_router)
