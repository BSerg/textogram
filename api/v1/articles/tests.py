#! coding: utf-8
from __future__ import unicode_literals

from collections import OrderedDict

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User, MultiAccount, MultiAccountUser
from articles.models import Article, ArticleContentText, ArticleContent


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
        self.multi_account = MultiAccount.objects.create(name='MULTI_ACCOUNT1', avatar='/tmp/avatar.jpg')
        self.multi_account_user = MultiAccountUser.objects.create(
            user=self.account,
            multi_account=self.multi_account,
            is_owner=True
        )
        self.article = Article.objects.create(
            owner=self.account,
            multi_account=self.multi_account,
            title='Hello, Article!',
            slug='hello-article',
            cover='/tmp/cover.png',
            html='<html/>',
            status=Article.PUBLISHED
        )
        self.another_article = Article.objects.create(
            owner=self.another_account,
            title='Hello, another Article!',
            slug='hello-another-article',
            cover='/tmp/cover.png',
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
        response = self.client.get('/api/v1/articles/editor/hello-article/')
        response.render()
        self.assertEqual(response.status_code, 401)

        response = self.client.patch('/api/v1/articles/editor/hello-article/', {'title': 'New'})
        response.render()
        self.assertEqual(response.status_code, 401)

        response = self.client.delete('/api/v1/articles/editor/hello-article/')
        response.render()
        self.assertEqual(response.status_code, 401)

    def test_another_user_retrieve_update_delete(self):
        self.client.force_authenticate(user=self.another_account)
        response = self.client.get('/api/v1/articles/editor/hello-article/')
        response.render()
        self.assertEqual(response.status_code, 403)

        response = self.client.patch('/api/v1/articles/editor/hello-article/', {'title': 'New'})
        response.render()
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/api/v1/articles/editor/hello-article/')
        response.render()
        self.assertEqual(response.status_code, 403)

    def test_retrieve(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.get('/api/v1/articles/editor/hello-article/')
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
        response = self.client.patch('/api/v1/articles/editor/hello-article/', {
            'title': 'NewNew',
        })
        response.render()
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.delete('/api/v1/articles/editor/hello-article/')
        response.render()
        self.article.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.article.status, Article.DELETED)


class ArticleContentTestCase(TestCase):
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
            first_name='Петр',
            last_name='Иванов',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='54321'
        )
        self.article = Article.objects.create(
            owner=self.account,
            title='Hello, Article!',
            slug='hello-article',
            cover='/tmp/cover.png',
            html='<html/>',
            status=Article.PUBLISHED
        )
        self.content_text = ArticleContentText.objects.create(
            article=self.article,
            position=0,
            text='Hello **WORLD**!'
        )
        self.token = Token.objects.create(user=self.account)
        self.client = APIClient()

    def test_retireve(self):
        self.client.force_authenticate(user=self.account, token=self.token)
        response = self.client.get('/api/v1/articles/content/1/')
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'article': 1,
            'position': 0,
            'text': 'Hello **WORLD**!',
        })

    def test_create(self):
        data = {
            'type': 1,
            'article': 1,
            'position': 0,
            'text': 'NEW TEXT'
        }
        self.client.force_authenticate(user=self.account, token=self.token)
        response = self.client.post('/api/v1/articles/content/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 201)
        c = ArticleContentText.objects.get(pk=response.data['id'])
        self.assertIsInstance(c, ArticleContentText)

        self.client.force_authenticate(user=self.another_account)
        response = self.client.post('/api/v1/articles/content/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/articles/content/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 401)

    def test_update(self):
        data = {
            'text': 'UPDATE TEXT'
        }
        self.client.force_authenticate(user=self.account, token=self.token)
        response = self.client.patch('/api/v1/articles/content/1/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['text'], data['text'])

        self.client.force_authenticate(user=self.another_account)
        response = self.client.post('/api/v1/articles/content/1/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/articles/content/1/', data, format='json')
        response.render()
        self.assertEqual(response.status_code, 401)

    def test_delete(self):
        self.client.force_authenticate(user=self.account, token=self.token)
        response = self.client.delete('/api/v1/articles/content/1/')
        response.render()
        self.assertEqual(response.status_code, 204)

        self.client.force_authenticate(user=self.another_account)
        response = self.client.post('/api/v1/articles/content/1/')
        response.render()
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/articles/content/1/')
        response.render()
        self.assertEqual(response.status_code, 401)

