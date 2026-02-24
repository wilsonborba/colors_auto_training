from typing import Optional

from core.logs import debug
from domain.services.ingestion_service import IngestionService

ingestion_service = IngestionService()


def create_keywords_handler(
    prompt: Optional[str] = None,
    user_query: Optional[str] = None,
    force_new_keywords: bool = False,
    limit: int = 20,
    offset: int = 0,
    ordered_by: str = "created_at",
    videos_extracted: Optional[bool] = False,
) -> list[str]:

    if force_new_keywords:
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

        debug(f"Saved keywords: {saved_keywords} | Missed keywords: {missed_keywords}")

    from_db_keywords = ingestion_service.get_keywords_from_db(
        query_search=user_query,
        videos_extracted=videos_extracted,
        limit=limit,
        offset=offset,
        ordered_by="created_at",
    )

    debug(f"Fetched keywords from DB: {from_db_keywords}")

    return from_db_keywords
