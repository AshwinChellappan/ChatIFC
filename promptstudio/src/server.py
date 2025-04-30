from fastapi import FastAPI
from api import prompt_studio_api
from core.config import settings

# FastAPI instance for all envs
# app = FastAPI(
#         docs_url='/docs',
#         title="Prompt Studio Service",
#         description="Prompt Studio Service",
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
# Include space management API router
app.include_router(prompt_studio_api.router)
