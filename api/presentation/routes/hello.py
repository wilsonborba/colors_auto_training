from core.utils.responses import MyResponse
from fastapi import APIRouter, Body, Query, Request, Response, status
from src.core.logs import debug, error

hello_router = APIRouter()


@hello_router.post("hello", response_model=MyResponse)
async def hello_from_api_post(
    request: Request,
    response: Response,
    name: str = Body(..., description="Name to greet"),
):
    debug(f"Received request to greet {name}")

    try:
        greeting = f"Hello, {name}!"
        response.status_code = status.HTTP_200_OK
        return MyResponse(
            data={"greeting": greeting},
            message="Greeting generated successfully",
        )
    except Exception as e:
        error(f"Error generating greeting: {e}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return MyResponse(
            data=None, message="Internal server error while generating greeting"
        )


@hello_router.get("hello", response_model=MyResponse)
async def hello_from_api_get(
    request: Request,
    response: Response,
    name: str = Query(..., description="Name to greet"),
):
    debug(f"Received request to greet {name}")

    try:
        greeting = f"Hello, {name}!"
        response.status_code = status.HTTP_200_OK
        return MyResponse(
            data={"greeting": greeting},
            message="Greeting generated successfully",
        )
    except Exception as e:
        error(f"Error generating greeting: {e}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return MyResponse(
            data=None, message="Internal server error while generating greeting"
        )
