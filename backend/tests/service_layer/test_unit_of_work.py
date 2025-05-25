from unittest.mock import MagicMock

import pytest

# Assuming SqlModelUnitOfWork will use a real session eventually,
# for now, we can test its interface adherence or mock its session.
from app.adapters.uow_sqlmodel import SqlModelUnitOfWork

# Import MockUnitOfWork for type hinting if needed, from conftest
from tests.conftest import MockUnitOfWork


def test_uow_commits_and_rollbacks_mock_session() -> None:
    """Test that SqlModelUnitOfWork calls commit and rollback on its session."""
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session

    uow = SqlModelUnitOfWork(session_factory=mock_session_factory)

    with uow:
        # Simulate some work
        pass

    # Check commit was called once, rollback not called
    assert mock_session.commit.call_count == 1
    assert not mock_session.rollback.called
    assert mock_session.close.call_count == 1

    # Reset for next test
    mock_session.reset_mock()

    # Test exception case
    with pytest.raises(Exception, match="Test Exception"):
        with uow:
            raise Exception("Test Exception")

    # Verify rollback was called, not commit
    assert not mock_session.commit.called
    assert mock_session.rollback.call_count == 1
    assert mock_session.close.call_count == 1


# Using MockUnitOfWork from conftest for these tests.
# The type hint should be MockUnitOfWork, not AbstractUnitOfWork, if we are accessing .committed etc.
def test_abstract_uow_context_manager_commits(mock_uow: MockUnitOfWork) -> None:
    """Test that the UoW context manager commits on success."""
    assert not mock_uow.committed
    with mock_uow:
        pass  # Simulate successful operation
    assert mock_uow.committed
    assert not mock_uow.rolled_back


def test_abstract_uow_context_manager_rollbacks_on_exception(
    mock_uow: MockUnitOfWork,
) -> None:
    """Test that the UoW context manager rolls back on exception."""
    assert not mock_uow.rolled_back
    with pytest.raises(Exception, match="Test error"):
        with mock_uow:
            raise Exception("Test error")
    assert mock_uow.rolled_back
    assert not mock_uow.committed
