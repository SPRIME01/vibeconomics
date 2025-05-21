\
import uuid
from pydantic import EmailStr, Field
from sqlmodel import SQLModel # SQLModel is used as a base for some of these DTOs in the original file

# Properties to return via API, id is always required
class UserPublic(SQLModel): # Kept SQLModel as base from original, can be changed to Pydantic BaseModel if no SQLModel features are used
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    full_name: str | None

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

# Properties to return via API, id is always required
class ItemPublic(SQLModel): # Kept SQLModel as base
    id: uuid.UUID
    title: str
    description: str | None
    owner_id: uuid.UUID

class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int

# Generic message
class Message(SQLModel):
    message: str

# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None # Typically user ID or email

class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

# Schemas that were originally in models.py and are for API interaction (request bodies)
# These were also added to domain, but API schemas can be slightly different (e.g. for validation)
# For now, they are direct copies or slightly adapted. If domain objects diverge, these can be maintained separately.

class UserCreateInput(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
    # is_active and is_superuser are typically set by backend, not taken from user input directly for creation

class UserRegisterInput(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

class UserUpdateInput(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None # Allow admin to update these
    is_superuser: bool | None = None

class UserUpdateMeInput(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)

class UpdatePasswordInput(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

class ItemCreateInput(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

class ItemUpdateInput(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

