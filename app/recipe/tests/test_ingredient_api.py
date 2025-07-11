"""
Tests for the Ingredient APIs
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)

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

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients assigned to recipes"""
        in1 = Ingredient.objects.create(user=self.user, name='Ingredient 1')
        in2 = Ingredient.objects.create(user=self.user, name='Ingredient 2')
        recipe = Recipe.objects.create(
            title='Recipe',
            time_minutes=5,
            price='5.05',
            user=self.user,
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """Test listing ingredients is a unique list"""
        ing = Ingredient.objects.create(user=self.user, name='Ingredient 1')
        Ingredient.objects.create(user=self.user, name='Ingredient 2')
        recipe1 = Recipe.objects.create(
            title='Recipe',
            time_minutes=5,
            price='5.05',
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Second Recipe',
            time_minutes=5,
            price='5.05',
            user=self.user,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
