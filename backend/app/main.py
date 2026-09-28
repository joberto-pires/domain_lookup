from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.jobs import router as jobs_router

app = FastAPI(title="Domain Lookup API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
