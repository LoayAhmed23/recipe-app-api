"""
Tests for the Recipe APIS
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create the url for the detail recipe URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create the url for the image upload URL"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a test recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 35,
        'price': Decimal('80.65'),
        'description': 'Test Recipe Description',
        'link': 'https://examplelink.com',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """create user for testing"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Unauthenticated API Requests Tests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retireve recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Authenticated API Requests Tests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com', password='password')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrievinng recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        selializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, selializer.data)

    def test_retrieve_recipes_limited_to_user(self):
        """Test retrievinng recipes is limited to authenticated user"""
        create_recipe(user=self.user)
        otheruser = create_user(email='testother@example.com',
                                password='password')
        create_recipe(user=otheruser)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        selializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, selializer.data)

    def test_get_recipe_detail(self):
        """Test revrieving recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """test creating a recipe"""
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 35,
            'price': Decimal('80.65'),
            'description': 'Test Recipe Description',
            'link': 'https://examplelink.com',
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        og_link = 'https://oldlink.com'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link=og_link
        )

        payload = {
            'title': 'NEW title',
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, og_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link='https://oldlink.com',
        )

        payload = {
            'title': 'New Recipe',
            'time_minutes': 355,
            'price': Decimal('800.65'),
            'description': 'New Recipe Description',
            'link': 'https://newlink.com',
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_error(self):
        """Test changing the user return an error"""
        newuser = create_user(email='testnew@example.com',
                                    password='password')
        recipe = create_recipe(self.user)

        payload = {
            'user': newuser.id
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting recipe"""
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test deleting another users recipe returns error"""
        newuser = create_user(email='testnew@example.com',
                                    password='password')
        recipe = create_recipe(user=newuser)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tag(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'New Recipe',
            'time_minutes': 355,
            'price': Decimal('800.65'),
            'link': 'https://examplelink.com',
            'tags': [{'name': 'Dessert'}, {'name': 'Vegan'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tag"""
        tag = Tag.objects.create(user=self.user, name='Vegan')
        payload = {
            'title': 'New Recipe',
            'time_minutes': 355,
            'price': Decimal('800.65'),
            'link': 'https://examplelink.com',
            'tags': [{'name': 'Dessert'}, {'name': 'Vegan'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Vegan'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(user=self.user, name='Vegan')
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_vegan = Tag.objects.create(user=self.user, name='Vegan')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_vegan)

        tag_dessert = Tag.objects.create(user=self.user, name='Dessert')
        payload = {'tags': [{'name': 'Dessert'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_dessert, recipe.tags.all())
        self.assertNotIn(tag_vegan, recipe.tags.all())

    def test_clear_repice_tags(self):
        """Test clearing recipe's tags"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            'title': 'New Recipe',
            'time_minutes': 355,
            'price': Decimal('800.65'),
            'link': 'https://examplelink.com',
            'ingredients': [{'name': 'Milk'}, {'name': 'Flour'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name='Water')
        payload = {
            'title': 'New Recipe',
            'time_minutes': 355,
            'price': '800.65',
            'link': 'https://examplelink.com',
            'ingredients': [{'name': 'Milk'}, {'name': 'Water'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating a ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Milk'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Milk')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Eggs')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Milk')
        payload = {'ingredients': [{'name': 'Milk'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_repice_ingredients(self):
        """Test clearing recipe's ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name='Milk')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test Filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title='Recipe 1')
        r2 = create_recipe(user=self.user, title='Recipe 2')
        tag1 = Tag.objects.create(user=self.user, name='Tag 1')
        tag2 = Tag.objects.create(user=self.user, name='Tag 2')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='Recipe 3')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test Filtering recipes by ingredients"""
        r1 = create_recipe(user=self.user, title='Recipe 1')
        r2 = create_recipe(user=self.user, title='Recipe 2')
        ing1 = Ingredient.objects.create(user=self.user, name='ingredient 1')
        ing2 = Ingredient.objects.create(user=self.user, name='ingredient 2')
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        r3 = create_recipe(user=self.user, title='Recipe 3')

        params = {'ingredients': f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPES_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTest(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com', password='password')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """"Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """"Test uploading an invalid image to a recipe"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'stringdata'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
