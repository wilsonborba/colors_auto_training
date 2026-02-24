from typing import Optional

from core.logs import debug
from domain.services.ingestion_service import IngestionService

ingestion_service = IngestionService()


def create_keywords_handler(
    prompt: Optional[str] = None, user_query: Optional[str] = None
) -> dict[str, list[str] | str]:

    keyword_json = ingestion_service.get_keywords_from_groq(
        user_query=user_query,
        prompt=prompt,
    ).model_dump()

    keywords = keyword_json.get("keywords", [])
    query = keyword_json.get("query", "")

    saved_keywords, missed_keywords = ingestion_service.save_keywords_to_db(
        keywords=keywords,
        query=query,
    )

    debug(f"Saved keywords: {saved_keywords}, Missed keywords: {missed_keywords}")

    return {"saved_keywords": saved_keywords, "missed_keywords": missed_keywords}
