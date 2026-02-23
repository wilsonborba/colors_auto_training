from typing import Optional

from core.settings import app_settings
from dal.remote.groq_adapter import GroqApiAdapter
from domain.models.groq_api_model import GroqResponseSchema


class IngestionService:
    def __init__(self):
        self.app_settings = app_settings()
        self.groq_api_adapter = GroqApiAdapter(
            api_key=self.app_settings.GROQ_API_KEY,
            model=self.app_settings.GROQ_MODEL,
            timeout_seconds=self.app_settings.GROQ_TIMEOUT,
            base_url=self.app_settings.GROQ_BASE_URL,
        )

    def get_keywords_from_groq(
        self, user_query: Optional[str] = None, prompt: Optional[str] = None
    ) -> GroqResponseSchema:

        if user_query is None:
            user_query = "Find me videos that contain persons using clothes"

        if prompt is None:
            prompt = (
                "Return me a safe video search list as strict JSON only. "
                'Schema: {"query": string, "keywords": string[], "negative_keywords": string[]}. '
                "Include negative keywords to reduce irrelevant results. "
                "Never create sexual, explicit, pornographic, child, toddler, kid, schoolgirl, teen, underage, or minors-focused intent. "
                "If user input is unsafe, sanitize it to a benign alternative query."
            )

        response = self.groq_api_adapter.query(user_query=user_query, prompt=prompt)
        return response
