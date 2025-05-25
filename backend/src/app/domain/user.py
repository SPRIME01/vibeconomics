import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr = Field(max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation - Considered domain as it defines a user structure
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on update, all are optional - Considered domain
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class UpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

    model_config = ConfigDict(from_attributes=True)


# Domain model for User - distinct from DB model
class User(UserBase):
    id: uuid.UUID
    # Hashed password is not part of the domain model for direct manipulation
    # items list would be handled by service layer, not directly part of this core domain model object
    model_config = ConfigDict(from_attributes=True)

    model_config = ConfigDict(from_attributes=True)
