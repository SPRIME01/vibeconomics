# filepath: c:\Users\sprim\FocusAreas\Projects\Dev\vibeconomics\backend\src\app\api\routes\items.py
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.domain.user import (
    User as DomainUser,  # Import domain User for type hinting current_user
)
from app.entrypoints.api import deps  # Adjusted import
from app.entrypoints.schemas import (
    ItemCreateInput,  # Renamed from ItemCreate
    ItemPublic,  # Renamed from Item to ItemPublic for response model
    ItemsPublic,
    ItemUpdateInput,  # Renamed from ItemUpdate
    Message,  # Renamed from User to UserPublic, assuming it's for response model
)

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: Annotated[
        Session, Depends(deps.get_db)
    ],  # Corrected session type hint and dependency
    current_user: Annotated[
        DomainUser, Depends(deps.get_current_user)
    ],  # Changed to deps.get_current_user and DomainUser
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items.
    """
    # ORM model Item should be used for DB queries, not ItemPublic schema
    from app.adapters.orm import Item as ORMItem

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(ORMItem)
        count = session.exec(count_statement).one()
        statement = select(ORMItem).offset(skip).limit(limit)
        items = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(ORMItem)
            .where(ORMItem.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(ORMItem)
            .where(ORMItem.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(
    session: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[
        DomainUser, Depends(deps.get_current_user)
    ],  # Changed to deps.get_current_user and DomainUser
    id: uuid.UUID,
) -> Any:
    """
    Get item by ID.
    """
    from app.adapters.orm import Item as ORMItem

    item = session.get(ORMItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[
        DomainUser, Depends(deps.get_current_user)
    ],  # Changed to deps.get_current_user and DomainUser
    item_in: ItemCreateInput,  # Corrected type hint
) -> Any:
    """
    Create new item.
    """
    # crud.create_item should be used here, it expects ItemCreateInput
    # and handles the owner_id association.
    item = crud.create_item(session=session, item_in=item_in, owner_id=current_user.id)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[
        DomainUser, Depends(deps.get_current_user)
    ],  # Changed to deps.get_current_user and DomainUser
    id: uuid.UUID,
    item_in: ItemUpdateInput,  # Corrected type hint
) -> Any:
    """
    Update an item.
    """
    from app.adapters.orm import Item as ORMItem

    item = session.get(ORMItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Use crud.update_item if available, or adapt logic here.
    # For now, direct update similar to original, but using item_in (ItemUpdateInput)
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)  # ORMItem has sqlmodel_update
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[
        DomainUser, Depends(deps.get_current_user)
    ],  # Changed to deps.get_current_user and DomainUser
    id: uuid.UUID,
) -> Message:
    """
    Delete an item.
    """
    from app.adapters.orm import Item as ORMItem

    item = session.get(ORMItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
