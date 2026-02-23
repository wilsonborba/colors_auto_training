from core.utils.responses import MyResponse
from fastapi import APIRouter, Body, Query, Request, Response, status
from src.core.logs import debug, error

keyword_router = APIRouter()


@keyword_router.get("/keywords", response_model=MyResponse)
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


@keyword_router.post("/keywords", response_model=MyResponse)
async def create_keyword(
    request: Request,
    response: Response,
    prompt: str = Body(..., description="Keyword to create"),
):
    debug(f"Received request to create keyword: {prompt}")

    try:
        # Here you would typically save the keyword to a database
        return MyResponse(
            data={"keyword": prompt},
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
