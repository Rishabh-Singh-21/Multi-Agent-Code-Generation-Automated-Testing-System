from __future__ import annotations
from abc import ABC, abstractmethod
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from configs.settings import settings


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(model=settings.openai_model, input=prompt)
        return response.output_text


class GeminiClient(LLMClient):
    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    def generate(self, prompt: str) -> str:
        return self.model.generate_content(prompt).text


class GroqClient(LLMClient):
    def __init__(self) -> None:
        self.client = Groq(api_key=settings.groq_api_key)

    def generate(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


class EchoClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return prompt


def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "openai" and settings.openai_api_key:
        return OpenAIClient()
    if provider == "gemini" and settings.gemini_api_key:
        return GeminiClient()
    if provider == "groq" and settings.groq_api_key:
        return GroqClient()
    return EchoClient()
