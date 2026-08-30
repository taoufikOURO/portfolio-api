"""Projects API routes."""

import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.project import Project, ProjectContributor, ProjectStack
from app.models.stack import Stack
from app.schemas.project import ProjectOut
from app.routers.auth import get_current_user
from app.core.storage import upload_image

router = APIRouter(prefix="/projects", tags=["projects"])


class ReorderItem(BaseModel):
    id: str
    order: int


class ReorderPayload(BaseModel):
    items: list[ReorderItem]


@router.get("/", response_model=list[ProjectOut])
def list_projects(db: DBSession = Depends(get_db)):
    return db.query(Project).order_by(Project.order.asc()).all()


@router.put("/reorder/batch")
def reorder_projects(
    payload: ReorderPayload,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    for item in payload.items:
        db.query(Project).filter(Project.id == item.id).update({"order": item.order})
    db.commit()
    return {"message": "Ordre mis à jour"}


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: DBSession = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    name: str = Form(...),
    description: str = Form(...),
    app_link: Optional[str] = Form(None),
    github_link: Optional[str] = Form(None),
    order: int = Form(0),
    stack_ids: str = Form("[]"),  # JSON stringifié, ex: '["id1", "id2"]'
    contributors: str = Form(
        "[]"
    ),  # JSON stringifié, ex: '[{"name": "...", "github_url": "..."}]'
    image: UploadFile = File(...),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stack_id_list = json.loads(stack_ids)
    contributors_list = json.loads(contributors)

    image_bytes = await image.read()
    picture_url = upload_image(image_bytes, image.filename, "projets")

    project = Project(
        name=name,
        description=description,
        app_link=app_link,
        github_link=github_link,
        picture=picture_url,
        order=order,
    )
    db.add(project)
    db.flush()

    if stack_id_list:
        stacks = db.query(Stack).filter(Stack.id.in_(stack_id_list)).all()
        if len(stacks) != len(stack_id_list):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs stacks sont introuvables"
            )
        project.project_stacks = [
            ProjectStack(stack_id=s.id, project_id=project.id) for s in stacks
        ]

    for contrib in contributors_list:
        db.add(
            ProjectContributor(
                name=contrib["name"],
                github_url=contrib["github_url"],
                project_id=project.id,
            )
        )

    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    app_link: Optional[str] = Form(None),
    github_link: Optional[str] = Form(None),
    order: Optional[int] = Form(None),
    stack_ids: Optional[str] = Form(None),
    contributors: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if app_link is not None:
        project.app_link = app_link
    if github_link is not None:
        project.github_link = github_link
    if order is not None:
        project.order = order

    if image is not None:
        image_bytes = await image.read()
        project.picture = upload_image(image_bytes, image.filename, "projets")

    if stack_ids is not None:
        stack_id_list = json.loads(stack_ids)
        stacks = db.query(Stack).filter(Stack.id.in_(stack_id_list)).all()
        if len(stacks) != len(stack_id_list):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs stacks sont introuvables"
            )
        project.project_stacks = [
            ProjectStack(stack_id=s.id, project_id=project.id) for s in stacks
        ]

    if contributors is not None:
        contributors_list = json.loads(contributors)
        project.contributors = [
            ProjectContributor(
                name=c["name"], github_url=c["github_url"], project_id=project.id
            )
            for c in contributors_list
        ]

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    db.delete(project)
    db.commit()
    return None
