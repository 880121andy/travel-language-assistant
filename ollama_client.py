import requests
from typing import List, Dict, Generator, Optional

OLLAMA_URL = "http://localhost:11434"

class OllamaClient:
    def __init__(self, model: str = "llama3", base_url: str = OLLAMA_URL, temperature: float = 0.7):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, options: Optional[Dict] = None) -> str:
        """Send a chat completion request to Ollama.

        messages: list of {role, content}
        stream: if True yields chunks (generator), else returns full string
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": options or {"temperature": self.temperature}
        }
        url = f"{self.base_url}/api/chat"
        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()

        if not stream:
            data = resp.json()
            return data.get("message", {}).get("content", "")

        def generator() -> Generator[str, None, None]:
            # For streaming, re-post with stream=True and iterate lines
            with requests.post(url, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        obj = requests.utils.json.loads(line.decode('utf-8'))
                        chunk = obj.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except Exception:
                        continue
        return generator()
