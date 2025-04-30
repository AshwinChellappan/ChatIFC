from fastapi import FastAPI
from api import space_instance_management_api
from api import space_management_api
from core.config import settings
from util.logger import Logger

logger = Logger()
# FastAPI instance for all environments
# app = FastAPI(
#         docs_url='/docs',
#         title="Space Management Service",
#         description="Space Management  Service",
#     )
app = FastAPI(
        swagger_ui_oauth2_redirect_url='/',
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": settings.AZURE_AD_CLIENT_ID,
            "scopes": [settings.AZURE_AD_SCOPE]
        },
        docs_url='/docs',
        title="Document Management Service",
        description="Document Management  Service",
    )
# print('starting application..')
logger.log('FastAPI app created...')
# Include space management API router
app.include_router(space_management_api.router)
app.include_router(space_instance_management_api.router)
