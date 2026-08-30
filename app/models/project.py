from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow


class Project(Base):
    __tablename__ = "project"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    app_link = Column(String, nullable=True)
    github_link = Column(String, nullable=True)
    picture = Column(String, nullable=False)
    order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project_stacks = relationship("ProjectStack", back_populates="project")
    contributors = relationship(
        "ProjectContributor", back_populates="project", cascade="all, delete-orphan"
    )

    @property
    def stacks(self):
        # transforme la liste de ProjectStack (table de jointure)
        # en liste directe de Stack, plus simple à consommer
        return [ps.stack for ps in self.project_stacks]


class ProjectContributor(Base):
    __tablename__ = "project_contributor"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    github_url = Column(String, nullable=False)

    project_id = Column(
        String, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="contributors")


class ProjectStack(Base):
    __tablename__ = "project_stack"

    project_id = Column(String, ForeignKey("project.id"), primary_key=True)
    stack_id = Column(String, ForeignKey("stack.id"), primary_key=True)

    project = relationship("Project", back_populates="project_stacks")
    stack = relationship("Stack", back_populates="project_stacks")
