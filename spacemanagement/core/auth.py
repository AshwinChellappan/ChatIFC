from fastapi import Depends, HTTPException, Request, status
from typing import Any
from models.user import User
from services.azure_ad_auth_service import authorize
from core.config import settings
from util.logger import Logger
import requests

logger = Logger()

class ForbiddenAccess(HTTPException):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(user: User = Depends(authorize)) -> User:
    return user

def get_user_groups(token):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        display_names = []
        url = settings.GRAPH_API_GROUP_MEMBER_URL

        while url:  # Keep fetching until there's no nextLink
            api_response = requests.get(url, headers=headers)

            if api_response.status_code == 200:
                data = api_response.json()
                
                # Add group display names to the list
                if "value" in data:
                    display_names.extend([group.get("displayName") for group in data["value"]])
                
                # Check for the nextLink to continue fetching
                url = data.get('@odata.nextLink', None)
            else:
                logger.log('Error in fetching response', api_response.status_code)
                break

        return display_names

    except Exception as e:
        logger.log(f"Request error occurred: {e}", 'ERROR')
        return []