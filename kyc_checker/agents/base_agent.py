"""Base class for all KYC agents."""

from abc import ABC, abstractmethod
from utils.groq_client import GroqClient


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, groq: GroqClient):
        self.groq = groq

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Execute the agent logic. Returns a result dict."""
        ...
