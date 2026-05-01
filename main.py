from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.infrastructure.database import init_db
from src.presentation.trade_license.router import router as trade_license_router
from src.presentation.auth.router import router as auth_router

# Initialize database tables
init_db()

# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="Trade License Workflow API",
    description=(
        "Domain-Driven Design + Clean Architecture implementation of the "
        "Trade License application lifecycle: Submit → Review → Approve."
    ),
    version="1.0.0",
    contact={"name": "Trade License Team"},
    license_info={"name": "MIT"},
)

app.include_router(trade_license_router)
app.include_router(auth_router)

# Mount the static frontend directory
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/health", tags=["System"])
def health_check() -> dict:
    return {"status": "ok"}
