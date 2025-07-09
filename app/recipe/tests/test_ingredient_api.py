"""
Tests for the Ingredient APIs
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='test@example.com', password='password'):
    return get_user_model().objects.create_user(email, password)


def detail_url(ingredient_id):
    """Create the url for the detail ingredient URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PublicTIngredientsAPITests(TestCase):
    """Unauthenticated API Requests Tests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retireve ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Authenticated API Requests Tests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrievinng Ingredients"""
        Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Milk')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        selializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, selializer.data)

    def test_retrieve_ingredients_limited_to_user(self):
        """Test retrieving ingredients is limited to authenticated user"""
        otheruser = create_user(email='testother@example.com')
        Ingredient.objects.create(user=otheruser, name='Milk')
        ingredient = Ingredient.objects.create(user=self.user, name='Eggs')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Milk')

        payload = {'name': 'Eggs'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredientg(self):
        """Test deleting ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Milk')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())
