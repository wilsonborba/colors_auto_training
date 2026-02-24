import datetime
from typing import Optional

from core.logs import debug, error
from core.settings import app_settings
from dal.local.db_adapter import DBAdapter
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
        self.db_adapter = DBAdapter()

    def get_keywords_from_db(
        self,
        query_search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        videos_extracted: Optional[bool] = False,
        ordered_by: str = "created_at",
    ) -> list[str]:

        filters = {}
        if query_search:
            filters["query_search"] = query_search
        if videos_extracted is not None:
            filters["videos_extracted"] = videos_extracted

        try:
            rows = self.db_adapter.read_where_many(
                "keywords",
                where=filters,
                limit=limit,
                offset=offset,
                order_by=[ordered_by],
            )
            keywords = [row["key_name"] for row in rows]
            return keywords
        except Exception as e:
            error(f"Error fetching keywords from DB: {e}")
            return []

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

    def save_keywords_to_db(
        self, keywords: list[str], query: str
    ) -> tuple[list[str], list[str]]:
        # Implement your DB saving logic here using self.db_adapter
        # For example, you might have a table with columns: id (auto), query (string), keyword (string)
        # def insert_row(self, table_name: str, data: dict, schema: str | None = None):

        added_keywords = []
        missed_keywords = []

        try:
            for keyword in keywords:
                inserted = self.db_adapter.insert_row(
                    "keywords",
                    {
                        "query_search": query,
                        "key_name": keyword,
                        "videos_extracted": False,
                    },
                    ignore=True,
                )

                if inserted:
                    added_keywords.append(keyword)
                else:
                    missed_keywords.append(keyword)

        except Exception as e:
            error(f"Error saving keywords to DB: {e}")
            raise

        return added_keywords, missed_keywords
