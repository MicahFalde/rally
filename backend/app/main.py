from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, campaigns, canvass, lookups, surveys, turfs, voters

app = FastAPI(
    title="Rally",
    description="Field operations platform for state legislative campaigns",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(voters.router, prefix="/api/v1")
app.include_router(turfs.router, prefix="/api/v1")
app.include_router(canvass.router, prefix="/api/v1")
app.include_router(surveys.router, prefix="/api/v1")
app.include_router(lookups.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rally"}
