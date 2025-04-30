import unittest
from fastapi import HTTPException, status
from services.azure_ad_auth_service import InvalidAuthorization, AzureADAuthorization
from unittest.mock import patch, MagicMock
import requests
from jose import jwt
from jose.exceptions import JWTError


class TestInvalidAuthorization(unittest.TestCase):

    def test_initialization_with_detail(self):
        # Arrange
        detail_message = "Invalid credentials"

        # Act
        exception = InvalidAuthorization(detail=detail_message)

        # Assert
        self.assertEqual(exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(exception.detail, detail_message)
        self.assertEqual(exception.headers, {"WWW-Authenticate": "Bearer"})
        self.assertIsInstance(exception, HTTPException)

    def test_initialization_without_detail(self):
        # Act
        exception = InvalidAuthorization()

        # Assert
        self.assertEqual(exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(exception.detail, "Unauthorized")
        self.assertEqual(exception.headers, {"WWW-Authenticate": "Bearer"})
        self.assertIsInstance(exception, HTTPException)


class TestAzureADAuthorization(unittest.IsolatedAsyncioTestCase):

    @patch.object(requests, 'get')
    def test_cache_aad_keys_success(self, mock_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'jwks_uri': 'https://example.com/keys'
        }
        mock_get.side_effect = [mock_response, mock_response]

        auth = AzureADAuthorization()
        auth.base_auth_url = 'https://example.com'

        # Act
        auth._cache_aad_keys()
        print("auth.aad_jwt_keys_cache",auth.aad_jwt_keys_cache)
        # Assert
        self.assertTrue(mock_get.call_count == 1)


    @patch.object(jwt, 'decode')
    @patch.object(AzureADAuthorization, '_get_token_key')
    @patch.object(AzureADAuthorization, '_get_key_id')
    def test_decode_token_success(self, mock_get_key_id, mock_get_token_key, mock_jwt_decode):
        # Arrange
        mock_get_key_id.return_value = 'key_id'
        mock_get_token_key.return_value = 'public_key'
        mock_jwt_decode.return_value = {'oid': 'user_id'}

        auth = AzureADAuthorization()

        # Act
        decoded_token = auth._decode_token('dummy_token')

        # Assert
        self.assertEqual(decoded_token['oid'], 'user_id')


    @patch.object(jwt, 'decode')
    @patch.object(AzureADAuthorization, '_get_token_key')
    @patch.object(AzureADAuthorization, '_get_key_id')
    def test_decode_token_invalid_token(self, mock_get_key_id, mock_get_token_key, mock_jwt_decode):
        # Arrange
        mock_get_key_id.return_value = 'key_id'
        mock_get_token_key.return_value = 'public_key'
        mock_jwt_decode.side_effect = JWTError('Invalid token')

        auth = AzureADAuthorization()

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth._decode_token('dummy_token')

        self.assertEqual(cm.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(cm.exception.detail), 'The token has some invalid claims')

    def test_validate_token_scopes_invalid(self):
        # Arrange
        auth = AzureADAuthorization()
        invalid_token = jwt.encode({'scp': 'other_scope'}, 'dummy_key', algorithm='HS256')

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth._validate_token_scopes(invalid_token)

        self.assertEqual(cm.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(cm.exception.detail), 'Missing a required scope')

    def test_get_user_from_token_valid(self):
        # Arrange
        decoded_token = {
            'oid': 'user_id',
            'name': 'John Doe',
            'upn': 'john.doe@example.com',
            'roles': ['IFC-chatifc-studio-superadmin'],
            'groups': ['group1', 'group2']
        }

        # Act
        user = AzureADAuthorization._get_user_from_token(decoded_token)

        # Assert
        self.assertEqual(user.id, 'user_id')
        self.assertEqual(user.name, 'John Doe')
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertEqual(user.roles, ['IFC-chatifc-studio-superadmin'])
        self.assertEqual(user.groups, ['group1', 'group2'])

    def test_get_user_from_token_missing_oid(self):
        # Arrange
        decoded_token = {}

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            AzureADAuthorization._get_user_from_token(decoded_token)

        self.assertEqual(cm.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(cm.exception.detail), 'Unable to extract user details from token')

