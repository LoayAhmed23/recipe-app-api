"""
User Api Tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django .urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_USER_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return Test user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Pulic User Api tests"""

    def setUp(self):
        self.client = APIClient()

    def test_user_success(self):
        """Test successfully creating a user"""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exist_error(self):
        """Test creating a user with existing email address"""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'name': 'Test User',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is given if password is less than 5 charachters"""
        payload = {
            'email': 'test@example.com',
            'password': 'pass',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """"Test Generate token for valid credintials"""
        user_data = {
            'email': 'test@example.com',
            'password': 'paassword',
            'name': 'Test User',
        }
        create_user(**user_data)

        payload = {
            'email': user_data['email'],
            'password': user_data['password'],
        }
        res = self.client.post(TOKEN_USER_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_bad_credentials(self):
        """Test return error if credentials are not correct"""
        user_data = {
            'email': 'test@example.com',
            'password': 'paassword',
            'name': 'Test User',
        }
        create_user(**user_data)
        payload = {
            'email': user_data['email'],
            'password': 'differentpassword',
        }
        res = self.client.post(TOKEN_USER_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_blank_password(self):
        """Test return error if password is blank"""
        user_data = {
            'email': 'test@example.com',
            'password': 'paassword',
            'name': 'Test User',
        }
        create_user(**user_data)
        payload = {
            'email': user_data['email'],
            'password': '',
        }
        res = self.client.post(TOKEN_USER_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test auth is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API requests that require auth"""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='password',
            name='test user'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """"Test retrieving profile for logged in users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowes(self):
        """Test POST is not allows for me"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user data"""
        payload = {
            'name': 'New name',
            'password': 'newpassword',
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
