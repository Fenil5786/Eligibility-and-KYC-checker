"""
Groq LLM client — thin wrapper around the Groq REST API
using the OpenAI-compatible /openai/v1/chat/completions endpoint.
"""

import json
import requests
from typing import Optional


class GroqClient:
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.api_key = api_key
        self.model   = model

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }

        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data    = response.json()
        content = data["choices"][0]["message"]["content"]
        return content

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> dict:
        """Convenience method that parses the response as JSON."""
        raw = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=1024,
            json_mode=True,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Attempt to extract JSON block
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"raw_response": raw, "error": "JSON parse failed"}
