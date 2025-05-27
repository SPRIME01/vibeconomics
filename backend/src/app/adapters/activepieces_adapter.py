from abc import ABC, abstractmethod
from typing import Any


class AbstractActivePiecesAdapter(ABC):
    """Abstract interface for ActivePieces workflow execution."""

    @abstractmethod
    def run_workflow(
        self, workflow_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Run an ActivePieces workflow.

        Args:
            workflow_id: The ID of the workflow to run.
            input_data: The input data for the workflow.

        Returns:
            A dictionary containing the result of the workflow execution.
        """
        pass


class ActivePiecesAdapter(AbstractActivePiecesAdapter):
    """
    Adapter for interacting with ActivePieces workflows.
    """

    def run_workflow(
        self, workflow_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Simulates running an ActivePieces workflow.

        Args:
            workflow_id: The ID of the workflow to run.
            input_data: The input data for the workflow.

        Returns:
            A dictionary indicating the result of the workflow execution.
        """
        return {
            "success": True,
            "workflow_id": workflow_id,
            "output": {
                "message": "Workflow executed successfully",
                "details": input_data,
            },
        }
