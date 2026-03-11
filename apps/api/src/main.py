from fastapi import FastAPI

from src.api.routes.email_webhook import router as email_router
from src.api.routes.health import router as health_router
from src.api.routes.leads import router as leads_router
from src.api.routes.messages import router as messages_router
from src.api.routes.scheduling import router as scheduling_router
from src.api.routes.sms import router as sms_router
from src.core.config import get_settings
from src.core.db import Base, engine
from src.core.startup import register_ringcentral_webhook, schedule_subscription_renewal, shutdown_scheduler
from src.schemas import models  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    register_ringcentral_webhook()
    schedule_subscription_renewal()


@app.on_event('shutdown')
def shutdown() -> None:
    shutdown_scheduler()


app.include_router(health_router)
app.include_router(leads_router)
app.include_router(messages_router)
app.include_router(sms_router)
app.include_router(email_router)
app.include_router(scheduling_router)
