"""
Flexible LLM Client - Switch between Claude, Groq, Ollama, Mistral AI para prueba local, dejar por un timepo el agente conversacoinal con mistral para luego pasar a usar algo super barato tipo slm en cloud
"""

import os
from typing import Optional

# Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # claude, groq, ollama

# ============================================================================
# CLAUDE CLIENT
# ============================================================================

class ClaudeClient:
    def __init__(self):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


# ============================================================================
# GROQ CLIENT
# ============================================================================

class GroqClient:
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Fast & free
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system} if system else None,
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


# ============================================================================
# OLLAMA CLIENT (Local)
# ============================================================================

class OllamaClient:
    def __init__(self, model: str = "llama2"):
        import ollama
        self.client = ollama
        self.model = model

    def generate(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        full_prompt = f"{system}\n\n{prompt}".strip() if system else prompt

        response = self.client.generate(
            model=self.model,
            prompt=full_prompt,
            stream=False,
        )

        return response["response"]


# ============================================================================
# FACTORY
# ============================================================================

def get_llm_client():
    """Get LLM client based on environment variable"""

    if LLM_PROVIDER == "claude":
        print("📍 Using Claude (API)")
        return ClaudeClient()

    elif LLM_PROVIDER == "groq":
        print("📍 Using Groq (API)")
        return GroqClient()

    elif LLM_PROVIDER == "ollama":
        print("📍 Using Ollama (Local)")
        return OllamaClient(model="llama2")

    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


# ============================================================================
# SIMPLE INTERFACE
# ============================================================================

_client = None


def generate(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    """Generate text using configured LLM provider"""
    global _client

    if _client is None:
        _client = get_llm_client()

    return _client.generate(prompt, system, max_tokens)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print(f"LLM Provider: {LLM_PROVIDER}")

    response = generate(
        prompt="¿Cuál es la capital de Chile?",
        system="Responde brevemente en español.",
    )

    print(f"\nResponse:\n{response}")
