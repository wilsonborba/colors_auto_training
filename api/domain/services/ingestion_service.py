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
            user_query = "List to me videos keywords that contain persons using clothes of diferent colors, but avoid irrelevant content."

        if prompt is None:
            prompt = (
                "Return me a safe video search list as strict JSON only. "
                'Schema: {"query": string, "keywords": string[]'
                "Keywords must be short search phrases of 1 to 3 words (not single broad terms unless necessary). "
                "Prefer 2-3 word combinations that keep context (e.g., 'colorful outfit', 'colorful party people', 'brand new jackets', 'beautiful shirts'). "
                "Generate many varied keywords (at least 20) and randomize them: mix colors, clothing items, and contexts, "
                "but keep them relevant to people wearing clothes with different colors. "
                "Avoid negative keywords to reduce irrelevant results. "
                "Never create sexual, explicit, pornographic, child, toddler, kid, schoolgirl, teen, underage, or minors-focused intent. "
                "If user input is unsafe, sanitize it to a benign alternative query."
            )

        response = self.groq_api_adapter.query(user_query=user_query, prompt=prompt)
        return response
