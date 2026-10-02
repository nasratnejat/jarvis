from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def ask(self, user_message, conversation=None):
        """
        Send a user message to the AI provider.

        Returns:
            str: Assistant response.
        """
        raise NotImplementedError