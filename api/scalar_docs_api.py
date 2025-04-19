from fastapi import APIRouter
from scalar_fastapi import get_scalar_api_reference

router = APIRouter(
    prefix="/docs",
    tags=["docs"],
)


@router.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="Scalar API",
    )