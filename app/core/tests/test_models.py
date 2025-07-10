""""
Model tests
"""
from decimal import Decimal

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='test@example.com', password='password'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successfull(self):
        """test for creating a user successfully"""
        email = 'test@example.com'
        password = 'password123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test new user's email is normalied"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@EXAmple.COM', 'Test2@example.com'],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='password123',
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_error(self):
        """Raise error if no Email is provided"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'password123')

    def test_create_superuser(self):
        """test creating superusers"""
        email = 'test3@example.com'
        password = 'password123'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password,
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe"""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='password',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tager')

        self.assertEqual(str(tag), 'Tager')

    def test_create_ingredient(self):
        """Test creating a ingredient"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='ingredient 1'
        )

        self.assertEqual(str(ingredient), 'ingredient 1')

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_uuid(self, mock_uuid):
        """Test generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
