import httpx
from app.core.config import settings

class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat(self, messages: list[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
            # Removed the "tools" parameter because it hangs the reasoning model
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            choices = data.get("choices", [])
            if choices:
                # We grab the content, ignore the hidden reasoning tokens
                return choices[0]["message"]["content"]
            return "No response generated."

llm_client = GroqClient()
