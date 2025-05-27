from pydantic import BaseModel


class Strategy(BaseModel):
    name: str
    description: str
    prompt: str


class StrategyNotFoundError(Exception):
    pass


class InvalidStrategyFormatError(Exception):
    pass


class StrategyService:
    """
    Service for managing and retrieving AI strategies.
    Strategies are pre-defined textual components that can be inserted into prompts
    to guide the AI's behavior or provide high-level instructions.
    """

    def __init__(self):
        # In a real implementation, this might load strategies from a configuration,
        # database, or file system.
        self._strategies: dict[str, str] = {
            "default_qa": "You are a helpful AI assistant. Answer the user's question based on the provided context.",
            "summarizer": "Summarize the following text concisely.",
            "creative_writer": "Write a creative piece based on the following themes and ideas.",
        }

    async def get_strategy(self, strategy_name: str) -> str | None:
        """
        Retrieves the content of a strategy by its name.

        Args:
            strategy_name: The name of the strategy to retrieve.

        Returns:
            The strategy content as a string if found, otherwise None.
        """
        # Simulate async operation if strategies were fetched from an external source
        # For this placeholder, it's a simple dict lookup.
        return self._strategies.get(strategy_name)

    async def list_strategies(self) -> list[str]:
        """
        Lists the names of all available strategies.

        Returns:
            A list of strategy names.
        """
        return list(self._strategies.keys())

    async def add_strategy(self, strategy_name: str, content: str) -> None:
        """
        Adds or updates a strategy.

        Args:
            strategy_name: The name of the strategy.
            content: The textual content of the strategy.
        """
        self._strategies[strategy_name] = content
        # In a real implementation, this would persist the change.
