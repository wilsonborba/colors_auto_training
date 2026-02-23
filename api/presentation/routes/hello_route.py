from core.logs import debug, error
from core.utils.responses import MyResponse, MyResponseModel
from fastapi import APIRouter, Body, Query, Request, Response, status

hello_router = APIRouter()


@hello_router.post("/hello", response_model=MyResponseModel)
async def hello_from_api_post(
    request: Request,
    response: Response,
    name: str = Body(..., description="Name to greet"),
):
    debug(f"Received request to greet {name}")

    try:
        greeting = f"Hello, {name}!"
        return MyResponse(
            data={"greeting": greeting},
            message="Greeting generated successfully",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        error(f"Error generating greeting: {e}")

        return MyResponse(
            data=None,
            message="Internal server error while generating greeting",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@hello_router.get("/hello", response_model=MyResponseModel)
async def hello_from_api_get(
    request: Request,
    response: Response,
    name: str = Query(..., description="Name to greet"),
):
    debug(f"Received request to greet {name}")

    try:
        greeting = f"Hello, {name}!"

        return MyResponse(
            data={"greeting": greeting},
            message="Greeting generated successfully",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        error(f"Error generating greeting: {e}")
        return MyResponse(
            data=None,
            message="Internal server error while generating greeting",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
