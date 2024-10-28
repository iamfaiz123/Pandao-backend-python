from uuid import UUID
from pydantic import BaseModel, Field
from typing_extensions import Optional, List
from enum import Enum


class BlogCreate(BaseModel):
    title: str = Field(..., description="The title of the blog post")
    description: str = Field(..., description="The description of the blog post")
    thumbnail_image: str = Field(..., description="The URL or path to the thumbnail image")
    published_by: str= Field(..., description="The name of the person who published the blog post")
    url:str = Field(..., description="post by")
