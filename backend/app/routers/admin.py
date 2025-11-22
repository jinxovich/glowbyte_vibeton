from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models, security, database

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(
    status: str = None,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(security.get_current_admin)
):
    query = db.query(models.User)
    if status:
        query = query.filter(models.User.status == status)
    return query.all()

@router.patch("/users/{user_id}/approve")
def approve_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(security.get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = models.UserStatus.APPROVED
    db.commit()
    return {"message": f"Пользователь {user.email} одобрен"}

@router.patch("/users/{user_id}/reject")
def reject_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(security.get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = models.UserStatus.REJECTED
    db.commit()
    return {"message": f"Пользователь {user.email} заблокирован"}