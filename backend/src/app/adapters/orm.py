import uuid
from pydantic import EmailStr # Required for User table
from sqlmodel import Field, Relationship, SQLModel, Session, create_engine, select # Added create_engine, select, Session

# Import config settings
from app.config import settings

# Import User model for init_db
# This might need to be adjusted if crud operations are also moved/refactored
# from app.adapters.orm import User # REMOVING THIS LINE - CAUSES CIRCULAR IMPORT
# from app.domain.user import UserCreate # This will be an issue, domain model.
# For init_db, we might need a specific input schema if UserCreate from domain is not suitable
# Or crud.create_user needs to be available/refactored.
# For now, let's assume a UserCreate schema will be available or adapted.
# We will need to address the UserCreate and crud.create_user dependency for init_db carefully.
from app.domain.user import UserCreate # Using an input DTO

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# make sure all SQLModel models are imported before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# For more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28
# SQLModel.metadata.create_all(engine) # This should be handled by Alembic

def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don\'t want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel
    # SQLModel.metadata.create_all(engine)

    # This part needs careful handling of dependencies.
    # crud.create_user will not be available directly like this.
    # This logic might move to a bootstrap script or a service.
    # For now, porting it with a placeholder for user creation.

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        # Placeholder for user creation.
        # In a clean architecture, this would likely involve a call to a service
        # which uses a repository.
        # For now, we'll assume a simplified direct creation or that this function
        # will be refactored further.
        print(f"Attempting to create superuser: {settings.FIRST_SUPERUSER}")
        # user_in = UserCreateInput( # Original used UserCreate from app.models
        #     email=settings.FIRST_SUPERUSER,
        #     password=settings.FIRST_SUPERUSER_PASSWORD,
        #     is_superuser=True, # This field was part of the old UserCreate, not in UserBase directly
        # )
        # This is a temporary simplification. The actual user creation
        # will need to be handled by the yet-to-be-refactored CRUD/service layer.
        # For the purpose of moving the function, we'll keep the structure.
        # The call to crud.create_user(session=session, user_create=user_in) must be replaced.

        # Temporary direct object creation for ORM User, this bypasses hashing and other logic in crud.create_user
        # THIS IS NOT PRODUCTION READY and needs to be replaced by a proper service call.
        from app.security import get_password_hash # Temporary import for hashing

        db_user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            is_superuser=True,
            full_name="Super User" # Default full_name
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        print(f"Superuser {settings.FIRST_SUPERUSER} created.")

# Database model, database table inferred from class name
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

# Database model, database table inferred from class name
class Item(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=255) # Added from ItemBase
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    # owner: User | None = Relationship(back_populates="items") # Original had ondelete=\"CASCADE\" on owner_id, which is good.
    # SQLModel handles cascade delete via the foreign_key constraint typically, or it can be specified in the relationship.
    # For now, relying on DB-level cascade via foreign_key. If issues arise, can add cascade_delete=True to Relationship.
    owner: User = Relationship(back_populates="items")
