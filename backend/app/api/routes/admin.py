import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_platform_admin
from app.models import User
from app.services.voter_import import import_voter_file

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/voter-files/import")
async def upload_voter_file(
    file: UploadFile,
    state_code: str,
    geocode: bool = False,
    admin: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload and import a voter file. Platform admin only."""
    state_code = state_code.upper()
    if len(state_code) != 2:
        raise HTTPException(status_code=400, detail="State code must be 2 letters")

    # Save uploaded file
    upload_dir = Path(settings.voter_file_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{state_code}_{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        stats = await import_voter_file(db, file_path, state_code, geocode=geocode)
        return {"status": "complete", "file": file.filename, **stats}
    finally:
        # Clean up uploaded file
        if file_path.exists():
            os.unlink(file_path)
