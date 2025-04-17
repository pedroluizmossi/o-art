from fastapi import Depends, APIRouter
from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefAccessTokenInfo, FiefAsync
from fief_client.integrations.fastapi import FiefAuth
from core.env_core import get_env_variable, Envs
from core.config_core import Config

config_instance = Config()
fief_instance = config_instance.Fief(config_instance)
domain_address = fief_instance.get_domain()

fief = FiefAsync(
    domain_address,
    get_env_variable(Envs.FIEF_CLIENT_ID),
    get_env_variable(Envs.FIEF_CLIENT_SECRET),
)

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