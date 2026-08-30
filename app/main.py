"""Main application entry point for the FastAPI project."""

from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.stacks import router as stacks_router
from app.routers.skills import router as skills_router
from app.routers.education import router as education_router
from app.routers.experience import router as experience_router
from app.routers.articles import router as articles_router
from app.routers.users import router as users_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(stacks_router)
app.include_router(skills_router)
app.include_router(education_router)
app.include_router(experience_router)
app.include_router(articles_router)
app.include_router(users_router)
