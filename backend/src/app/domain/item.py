import uuid

from pydantic import BaseModel, Field


# Shared properties
class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

    class Config:
        from_attributes = True


# Properties to receive on item creation - Considered domain
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update - Considered domain
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)


# Domain model for Item - distinct from DB model
class Item(ItemBase):
    id: uuid.UUID
    owner_id: (
        uuid.UUID
    )  # Keep owner_id as it's a crucial piece of information for the item

    class Config:
        from_attributes = True
