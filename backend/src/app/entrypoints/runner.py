import logging
import typer
from typing_extensions import Annotated

from sqlmodel import Session
from sqlalchemy import Engine
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from sqlmodel import select

from app.adapters.orm import engine as default_engine, init_db as initialize_database
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

runner_app = typer.Typer()

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
# Renamed from init to avoid conflict with Typer's internal init
def pre_start_db_check(db_engine: Engine) -> None:
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            session.exec(select(1))
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        raise

@runner_app.command()
def pre_start(
    db_engine: Annotated[Engine, typer.Option(help="Database engine to use.")] = default_engine
) -> None:
    """Checks if the database is awake and ready."""
    logger.info("Initializing service - DB check")
    pre_start_db_check(db_engine)
    logger.info("Service finished initializing - DB check complete")

@runner_app.command()
def create_initial_data(
    db_engine: Annotated[Engine, typer.Option(help="Database engine to use.")] = default_engine
) -> None:
    """Creates initial data in the database, including a default superuser."""
    logger.info("Creating initial data")
    with Session(db_engine) as session:
        initialize_database(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    runner_app()
