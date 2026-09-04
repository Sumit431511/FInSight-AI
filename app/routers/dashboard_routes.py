"""
Admin Dashboard Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.auth.auth import get_current_user
from app.rag_evaluator.dashboard import get_dashboard_data

router = APIRouter()


@router.get("/dashboard")
def dashboard(user=Depends(get_current_user)):
    if user["role"] != "C-Level":
        raise HTTPException(
            status_code=403,
            detail="Only C-Level can access dashboard.",
        )

    return get_dashboard_data()
