"""
Tests for the Tag APIs
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe
)

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def create_user(email='test@example.com', password='password'):
    return get_user_model().objects.create_user(email, password)


def detail_url(tag_id):
    """Create the url for the detail tag URL"""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagsAPITests(TestCase):
    """Unauthenticated API Requests Tests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retireve tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Authenticated API Requests Tests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrievinng Tags"""
        Tag.objects.create(user=self.user, name='vegan')
        Tag.objects.create(user=self.user, name='dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        selializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, selializer.data)

    def test_retrieve_recipes_limited_to_user(self):
        """Test retrievinng tags is limited to authenticated user"""
        otheruser = create_user(email='testother@example.com')
        Tag.objects.create(user=otheruser, name='dessert')
        tag = Tag.objects.create(user=self.user, name='vegan')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating tag"""
        tag = Tag.objects.create(user=self.user, name='vegan')

        payload = {'name': 'New tag'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting tag"""
        tag = Tag.objects.create(user=self.user, name='vegan')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Tag 1')
        tag2 = Tag.objects.create(user=self.user, name='Tag 2')
        recipe = Recipe.objects.create(
            title='Recipe',
            time_minutes=5,
            price='5.05',
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """Test listing tags is a unique list"""
        tag = Tag.objects.create(user=self.user, name='Tag 1')
        Tag.objects.create(user=self.user, name='Tag 2')
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
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
