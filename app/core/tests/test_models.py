""""
Model tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


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
