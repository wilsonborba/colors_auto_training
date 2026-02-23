from typing import Optional

from domain.services.ingestion_service import IngestionService

ingestion_service = IngestionService()


def create_keywords_handler(
    prompt: Optional[str] = None, user_query: Optional[str] = None
) -> str:

    return ingestion_service.get_keywords_from_groq(
        user_query=user_query,
        prompt=prompt,
    ).model_dump()
