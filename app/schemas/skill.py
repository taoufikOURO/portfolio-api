from pydantic import BaseModel


class SkillBase(BaseModel):
    name: str


class SkillCreate(SkillBase):
    pass


class SkillOut(SkillBase):
    id: str

    class Config:
        from_attributes = True
