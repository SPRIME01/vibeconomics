from typing import Any


class ContextService:
    """
    Service for managing and retrieving contextual information.
    Context can be domain-specific data, user profiles, or any other information
    that can help tailor the AI's responses.
    """

    def __init__(self):
        # In a real implementation, this might load context from various sources
        # like databases, APIs, or configuration files.
        self._contexts: dict[str, Any] = {
            "general_knowledge": "This is a general knowledge context. The AI should use its broad training.",
            "financial_data_2023": "Context related to financial data up to the end of 2023.",
            "product_catalog_electronics": "Information about electronic products available in the catalog.",
        }

    async def get_context_content(self, context_name: str) -> str | None:
        """
        Retrieves the content for a given context name.

        Args:
            context_name: The name of the context to retrieve.

        Returns:
            The context content as a string if found, otherwise None.
            The content could be a simple string, a JSON string, or any other
            format that the AI pattern and templates are designed to work with.
        """
        # Simulate async operation if context were fetched from an external source.
        # For this placeholder, it's a simple dict lookup.
        # In a real scenario, this might involve database queries, API calls, etc.
        return self._contexts.get(context_name)

    async def list_contexts(self) -> list[str]:
        """
        Lists the names of all available contexts.

        Returns:
            A list of context names.
        """
        return list(self._contexts.keys())

    async def add_context(self, context_name: str, content: Any) -> None:
        """
        Adds or updates a context.

        Args:
            context_name: The name of the context.
            content: The content of the context. This could be a string,
                     dict, or any other data structure.
        """
        self._contexts[context_name] = content
        # In a real implementation, this would persist the change.
