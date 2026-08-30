"""Stack management endpoints for the FastAPI project."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from typing import Optional

from app.core.database import get_db
from app.models.stack import Stack
from app.schemas.stack import StackOut
from app.routers.auth import get_current_user
from app.core.storage import upload_image

router = APIRouter(prefix="/stacks", tags=["stacks"])


@router.get("/", response_model=list[StackOut])
def list_stacks(db: DBSession = Depends(get_db)):
    return db.query(Stack).order_by(Stack.order.asc()).all()


@router.get("/{stack_id}", response_model=StackOut)
def get_stack(stack_id: str, db: DBSession = Depends(get_db)):
    stack = db.query(Stack).filter(Stack.id == stack_id).first()
    if not stack:
        raise HTTPException(status_code=404, detail="Stack introuvable")
    return stack


@router.post("/", response_model=StackOut, status_code=201)
async def create_stack(
    name: str = Form(...),
    order: int = Form(0),
    image: UploadFile = File(...),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    picture_url = upload_image(await image.read(), image.filename, "stack")

    stack = Stack(name=name, picture=picture_url, order=order)
    db.add(stack)
    db.commit()
    db.refresh(stack)
    return stack


@router.put("/{stack_id}", response_model=StackOut)
async def update_stack(
    stack_id: str,
    name: Optional[str] = Form(None),
    order: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stack = db.query(Stack).filter(Stack.id == stack_id).first()
    if not stack:
        raise HTTPException(status_code=404, detail="Stack introuvable")

    if name is not None:
        stack.name = name
    if order is not None:
        stack.order = order
    if image is not None:
        stack.picture = upload_image(await image.read(), image.filename, "stack")

    db.commit()
    db.refresh(stack)
    return stack


@router.delete("/{stack_id}", status_code=204)
def delete_stack(
    stack_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stack = db.query(Stack).filter(Stack.id == stack_id).first()
    if not stack:
        raise HTTPException(status_code=404, detail="Stack introuvable")
    db.delete(stack)
    db.commit()
    return None
