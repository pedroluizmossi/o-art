from api.auth_api import router_metadata as auth_metadata
from api.image_api import router_metadata as image_metadata
from api.model_api import router_metadata as model_metadata
from api.plan_api import router_metadata as plan_metadata
from api.webhook_api import router_metadata as webhook_metadata
from api.websocket_api import router_metadata as websocket_metadata
from api.workflow_api import router_metadata as workflow_metadata

tags_metadata = [
    auth_metadata,
    image_metadata,
    workflow_metadata,
    model_metadata,
    plan_metadata,
    webhook_metadata,
    websocket_metadata,
]