from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.contribute import router as contribute_router
from routes.status import router as status_router

app = FastAPI(title="PatchPilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contribute_router, prefix="/api")
app.include_router(status_router,     prefix="/api")
