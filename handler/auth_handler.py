import uuid
from typing import Dict, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fief_client import FiefAccessTokenInfo, FiefAsync, FiefUserInfo
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