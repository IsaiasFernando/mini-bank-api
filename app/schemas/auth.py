from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserCreate(BaseModel):
    name: Name
    email: EmailStr
    password: Password


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
