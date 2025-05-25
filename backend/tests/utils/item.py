from sqlmodel import Session

from app import crud
from app.adapters.orm import Item
from app.entrypoints.schemas import ItemCreateInput  # Corrected name
from tests.utils.user import create_random_user  # Corrected path
from tests.utils.utils import random_lower_string  # Corrected path


def create_random_item(db: Session) -> Item:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreateInput(title=title, description=description)  # Corrected name
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id)
