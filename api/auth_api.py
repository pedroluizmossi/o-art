from fastapi import Depends, APIRouter
from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefAccessTokenInfo
from fief_client.integrations.fastapi import FiefAuth
from handler.auth_handler import domain_address, fief

scheme = OAuth2AuthorizationCodeBearer(
    domain_address + "/authorize",
    domain_address + "/api/token",
    scopes={"openid": "openid", "offline_access": "offline_access"},
    auto_error=False,
)

auth = FiefAuth(fief, scheme)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get("/user")
async def get_user(
        access_token_info: FiefAccessTokenInfo = Depends(auth.authenticated()),
):
    return access_token_info
