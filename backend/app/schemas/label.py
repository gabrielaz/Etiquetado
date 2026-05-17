from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class LabelSchemaBase(BaseModel):
    name: str
    color: str = "#3B82F6"
    description: Optional[str] = None
    shortcut: Optional[str] = None


class LabelSchemaCreate(LabelSchemaBase):
    pass


class LabelSchemaUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    shortcut: Optional[str] = None


class LabelSchemaOut(LabelSchemaBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WordLabelCreate(BaseModel):
    label_schema_id: int


class WordLabelOut(BaseModel):
    id: int
    word_id: int
    label_schema_id: int
    label_name: str
    label_color: str
    created_at: datetime

    class Config:
        from_attributes = True
