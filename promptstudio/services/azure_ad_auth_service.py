import base64
import requests
import rsa
from typing import Any, Dict, Mapping, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from core.config import settings
from models.user import User
from util.logger import Logger
from util.constants import URL

logger = Logger()

class InvalidAuthorization(HTTPException):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


class AzureADAuthorization(OAuth2AuthorizationCodeBearer):
    # cached AAD jwt keys
    # aad_jwt_keys_cache: dict = {}
    aad_jwt_keys_cache: Dict[str,bytes] = {}

    def __init__(self, aad_instance: str = settings.AZURE_AD_INSTANCE, aad_tenant: str = settings.AZURE_AD_TENANT_ID, auto_error: bool = True):
        logger.log('Azure AD Auth started...')
        self.scopes = ['user_impersonation']
        self.base_auth_url: str = f"{aad_instance}/{aad_tenant}"
        super(AzureADAuthorization, self).__init__(
            authorizationUrl = URL.OAUTH2_AUTH.format(tenant_id = settings.AZURE_AD_TENANT_ID),
            tokenUrl = URL.OAUTH2_TOKEN.format(tenant_id = settings.AZURE_AD_TENANT_ID),
            scopes = {settings.AZURE_AD_SCOPE : 'user_impersonation'},
            auto_error=auto_error
        )
        self.jwks_uri = URL.JWKS_URI.format(tenant_id = settings.AZURE_AD_TENANT_ID)

    async def __call__(self, request: Request) -> User:
        token: str = await super(AzureADAuthorization, self).__call__(request) or ''
        self._validate_token_scopes(token)
        logger.log('Token scopes validated...')
        decoded_token = self._decode_token(token)
        logger.log('Token decoded...')
        return self._get_user_from_token(decoded_token)

    @staticmethod
    def _get_user_from_token(decoded_token: Mapping) -> User:
        try:
            user_id = decoded_token['oid']
        except KeyError:
            logger.log('ERROR: Unable to extract user details from token','ERROR')
            raise InvalidAuthorization(detail='Unable to extract user details from token')
        logger.log('User details extracted...')
        return User(
            id=user_id,
            userId=user_id,
            name=decoded_token.get('name', ''),
            email=decoded_token.get('upn', ''),
            roles=decoded_token.get('roles', []),
            groups=decoded_token.get('groups', [])
        )

    @staticmethod
    def _get_validation_options() -> Dict[str, bool]:
        return {
            'require_aud': True,
            'require_exp': True,
            'require_iss': True,
            'require_iat': True,
            'require_nbf': True,
            'require_sub': True,
            'verify_aud': True,
            'verify_exp': True,
            'verify_iat': True,
            'verify_iss': True,
            'verify_nbf': True,
            'verify_sub': True,
        }

    def _validate_token_scopes(self, token: str):
        """
        Validate that the requested scopes are in the tokens claims
        """
        try:
            claims = jwt.get_unverified_claims(token) or {}
            token_scopes = claims.get('scp', '').split(' ')
        except (AttributeError, KeyError):
            logger.log('Malformed token or scopes.')
            raise InvalidAuthorization('Malformed token received')

        for scope in self.scopes:
            if scope not in token_scopes:
                raise InvalidAuthorization('Missing a required scope')

    @staticmethod
    def _get_key_id(token: str) -> Optional[str]:
        headers = jwt.get_unverified_header(token)
        return headers['kid'] if headers and 'kid' in headers else None

    @staticmethod
    def _ensure_b64padding(key: str) -> str:
        """
        The base64 encoded keys are not always correctly padded, so pad with the right number of =
        """
        key = key.encode('utf-8')
        missing_padding = len(key) % 4
        for _ in range(missing_padding):
            key += b'='
        return key

    def _cache_aad_keys(self) -> None:
        """
        Cache all AAD JWT keys - so we don't have to make a web call each auth request
        """
        response = requests.get(f"{self.base_auth_url}/v2.0/.well-known/openid-configuration")
        # Get AAD metadata
        aad_metadata = response.json() if response.ok else None
        jwks_uri = aad_metadata['jwks_uri'] if aad_metadata and 'jwks_uri' in aad_metadata else None
        if jwks_uri and self.validate_jwks_uri(jwks_uri):
            # Get response
            response = requests.get(f'{self.jwks_uri}')
            keys = response.json() if response.ok else None
            if keys and 'keys' in keys:
                for key in keys['keys']:
                    n = int.from_bytes(base64.urlsafe_b64decode(self._ensure_b64padding(key['n'])), "big")
                    e = int.from_bytes(base64.urlsafe_b64decode(self._ensure_b64padding(key['e'])), "big")
                    pub_key = rsa.PublicKey(n, e)
                    # Cache the PEM formatted public key.
                    AzureADAuthorization.aad_jwt_keys_cache[key['kid']] = pub_key.save_pkcs1()

    def validate_jwks_uri(self, jwks_uri):
        valid_jwks_uri = False
        if jwks_uri == self.jwks_uri:
            valid_jwks_uri = True
        
        return valid_jwks_uri

    def _get_token_key(self, key_id: str) -> str:
        if key_id not in AzureADAuthorization.aad_jwt_keys_cache:
            self._cache_aad_keys()
        return AzureADAuthorization.aad_jwt_keys_cache[key_id]

    def _decode_token(self, token: str) -> Mapping:
        key_id = self._get_key_id(token)
        if not key_id:
            raise InvalidAuthorization('The token does not contain kid')

        key = self._get_token_key(key_id)
        try:
            options = self._get_validation_options()
            return jwt.decode(token=token, key=key, algorithms=['RS256'], audience=settings.API_AUDIENCE, options=options)
        except (JWTClaimsError,ExpiredSignatureError, JWTError) as e:
            logger.log(f'Token validation error: {e}')
            raise InvalidAuthorization('The token has some invalid claims')
        except Exception as e:
            logger.log(f'Unexpected error during token decoding: {e}')
            raise InvalidAuthorization('Unable to decode token')


authorize = AzureADAuthorization()