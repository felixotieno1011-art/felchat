import httpx
import json
from app.core.config import settings

class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def stream_chat(self, messages: list[dict]):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
            "tools": [{"type": "browser_search"}],
            "tool_choice": "auto",
            "stream": True  # <-- The magic word
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            if "content" in delta and delta["content"] is not None:
                                yield delta["content"]
                        except Exception:
                            pass

llm_client = GroqClient()
