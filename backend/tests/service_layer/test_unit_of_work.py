from unittest.mock import MagicMock, patch
import pytest

from app.service_layer.unit_of_work import AbstractUnitOfWork
# Assuming SqlModelUnitOfWork will use a real session eventually,
# for now, we can test its interface adherence or mock its session.
from app.adapters.uow_sqlmodel import SqlModelUnitOfWork
# Import MockUnitOfWork for type hinting if needed, from conftest
from backend.tests.conftest import MockUnitOfWork


def test_uow_commits_and_rollbacks_mock_session() -> None:
    """Test that SqlModelUnitOfWork calls commit and rollback on its session."""
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session

    uow = SqlModelUnitOfWork(session_factory=mock_session_factory)

    with uow:
        # Simulate some work
        pass
    assert mock_session.commit.called_once
    assert not mock_session.rollback.called
    assert mock_session.close.called_once # Should be called once after successful context

    mock_session.reset_mock() # Reset call counts for all attributes of the mock

    with pytest.raises(Exception, match="Test Exception"):
        with uow: # New session created and closed here
            raise Exception("Test Exception")
    
    assert not mock_session.commit.called # Commit should not be called on exception
    assert mock_session.rollback.called_once # Rollback should be called
    assert mock_session.close.called_once # Session from this context should be closed once

# Using MockUnitOfWork from conftest for these tests.
# The type hint should be MockUnitOfWork, not AbstractUnitOfWork, if we are accessing .committed etc.
def test_abstract_uow_context_manager_commits(mock_uow: MockUnitOfWork) -> None:
    """Test that the UoW context manager commits on success."""
    assert not mock_uow.committed 
    with mock_uow:
        pass # Simulate successful operation
    assert mock_uow.committed
    assert not mock_uow.rolled_back

def test_abstract_uow_context_manager_rollbacks_on_exception(mock_uow: MockUnitOfWork) -> None:
    """Test that the UoW context manager rolls back on exception."""
    assert not mock_uow.rolled_back
    with pytest.raises(Exception, match="Test error"):
        with mock_uow:
            raise Exception("Test error")
    assert mock_uow.rolled_back
    assert not mock_uow.committed
