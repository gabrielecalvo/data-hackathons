from fastapi import FastAPI

from app.routes.api import api_router
from app.routes.website import website_router

app = FastAPI(
    title="Data Hackathon API",
    version="0.0.1",
    description="API to serve and document Data Hackathons",
)
app.include_router(website_router)
app.include_router(api_router)
