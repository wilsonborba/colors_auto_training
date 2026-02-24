from typing import Optional

from core.logs import debug, error
from core.utils.responses import MyResponse, MyResponseModel
from fastapi import APIRouter, Body, Query, Request, Response, status
from presentation.handlers.keyword_handler import create_keywords_handler

keyword_router = APIRouter()


@keyword_router.get("/keywords", response_model=MyResponseModel)
async def get_keywords(
    request: Request,
    response: Response,
):
    debug("Received request to get keywords")

    try:
        keywords = ["keyword1", "keyword2", "keyword3"]  # Example keywords
        return MyResponse(
            data={"keywords": keywords},
            message="Keywords retrieved successfully",
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        error(f"Error retrieving keywords: {e}")
        return MyResponse(
            data=None,
            message="Internal server error while retrieving keywords",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@keyword_router.post("/keywords", response_model=MyResponseModel)
async def create_keyword(
    request: Request,
    response: Response,
    prompt: Optional[str] = Body(None, description="Prompt to generate keywords from"),
    user_query: Optional[str] = Body(
        None, description="User query to generate keywords from"
    ),
    force_new_keywords: bool = Body(
        False, description="Whether to force generation of new keywords from the prompt"
    ),
    limit: int = Body(20, description="Number of keywords to return"),
    offset: int = Body(0, description="Offset for pagination"),
    ordered_by: str = Body(
        "created_at", description="Field to order keywords by (e.g., 'created_at')"
    ),
    videos_extracted: Optional[bool] = Body(
        False, description="Whether to filter keywords by videos extracted status"
    ),
):
    debug(f"Received request to create keyword: {prompt}")

    try:
        keywords = create_keywords_handler(
            prompt=prompt,
            user_query=user_query,
            force_new_keywords=force_new_keywords,
            limit=limit,
            offset=offset,
            ordered_by=ordered_by,
        )

        return MyResponse(
            data=keywords,
            message="Keyword created successfully",
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        error(f"Error creating keyword: {e}")
        return MyResponse(
            data=None,
            message="Internal server error while creating keyword",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
