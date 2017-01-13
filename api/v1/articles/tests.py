#! coding: utf-8
from __future__ import unicode_literals

from collections import OrderedDict

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User, MultiAccount, MultiAccountUser
from articles.models import Article, ArticleImage


class ArticleViewSetTestCase(TestCase):
    def setUp(self):
        self.account = User.objects.create(
            username='user',
            first_name='Иван',
            last_name='Петров',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='12345'
        )
        self.another_account = User.objects.create(
            username='another_user',
            first_name='Василий',
            last_name='Иванов',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='54321'
        )
        self.article = Article.objects.create(
            owner=self.account,
            slug='hello-article',
            content={'title': 'Hello, Article', 'cover': None, 'blocks': []},
            html='<html/>',
            status=Article.PUBLISHED
        )
        self.cover = ArticleImage.objects.create(article=self.article, image='/tmp/cover.png')
        self.article.content['cover'] = self.cover.id
        self.article.save()
        self.another_article = Article.objects.create(
            owner=self.another_account,
            slug='hello-another-article',
            content={'title': 'Hello, another Article', 'cover': None, 'blocks': []},
            html='<html/>'
        )

        self.token = Token.objects.create(user=self.account)
        self.client = APIClient()

    def test_public_retrieve(self):
        response = self.client.get('/api/v1/articles/hello-article/')
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, OrderedDict)

    def test_public_list(self):
        response = self.client.get('/api/v1/articles/')
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_anon_retrieve_update_delete(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/articles/editor/1/')
        response.render()
        self.assertEqual(response.status_code, 401)

        response = self.client.patch('/api/v1/articles/editor/1/', {'title': 'New'})
        response.render()
        self.assertEqual(response.status_code, 401)

        response = self.client.delete('/api/v1/articles/editor/1/')
        response.render()
        self.assertEqual(response.status_code, 401)

    def test_another_user_retrieve_update_delete(self):
        self.client.force_authenticate(user=self.another_account)
        response = self.client.get('/api/v1/articles/editor/%d/' % self.article.id)
        response.render()
        self.assertEqual(response.status_code, 403)

        response = self.client.patch('/api/v1/articles/editor/%d/' % self.article.id, {'title': 'New'})
        response.render()
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/api/v1/articles/editor/%d/' % self.article.id)
        response.render()
        self.assertEqual(response.status_code, 403)

    def test_retrieve(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.get('/api/v1/articles/editor/%d/' % self.article.id)
        response.render()
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.post('/api/v1/articles/editor/', {
            'title': 'New',
            'slug': 'new'
        })
        response.render()
        self.assertEqual(response.status_code, 201)

    def test_update(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.patch('/api/v1/articles/editor/%d/' % self.article.id, {
            'title': 'NewNew',
        })
        response.render()
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.delete('/api/v1/articles/editor/%d/' % self.article.id)
        response.render()
        self.article.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.article.status, Article.DELETED)


