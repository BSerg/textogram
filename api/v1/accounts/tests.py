#! coding: utf-8
from __future__ import unicode_literals

from collections import OrderedDict
from unittest import skip

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient, APITestCase

from accounts.models import User, MultiAccount, MultiAccountUser, PhoneCode
from api.v1.accounts.serializers import UserSerializer, PublicUserSerializer
from api.v1.accounts.views import PublicUserViewSet, UserViewSet, RegistrationView


class AccountSerializerTestCase(TestCase):
    def setUp(self):
        self.account = User.objects.create(
            username='test',
            first_name='Иван',
            last_name='Петров',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='12345'
        )
        self.multi_account1 = MultiAccount.objects.create(name='MULTI_ACCOUNT1', avatar='/tmp/avatar.jpg')
        self.multi_account2 = MultiAccount.objects.create(name='MULTI_ACCOUNT2', avatar='/tmp/avatar.jpg')
        self.multi_account_user_1 = MultiAccountUser.objects.create(
            user=self.account,
            multi_account=self.multi_account1,
            is_owner=True
        )
        self.multi_account_user_2 = MultiAccountUser.objects.create(
            user=self.account,
            multi_account=self.multi_account1,
            is_active=False
        )

    def test_main_serialiser_fields(self):
        serializer = UserSerializer(self.account)
        self.assertEqual(serializer.data, {
            'id': self.account.id,
            'first_name': 'Иван',
            'last_name': 'Петров',
            'avatar': '/data/tmp/avatar.jpg',
            'social': 'vk',
            'uid': '12345',
            'email': '',
            'multi_accounts': [
                OrderedDict([
                    ('name', 'MULTI_ACCOUNT1'),
                    ('avatar', '/data/tmp/avatar.jpg'),
                    ('is_owner', True)
                ]),
            ]
        })

    def test_public_serialiser_fields(self):
        serializer = PublicUserSerializer(self.account)
        self.assertEqual(serializer.data, {
            'id': self.account.id,
            'first_name': 'Иван',
            'last_name': 'Петров',
            'avatar': '/data/tmp/avatar.jpg',
        })


class UserViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.account = User.objects.create(
            username='test',
            first_name='Иван',
            last_name='Петров',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='12345'
        )
        self.token = Token.objects.create(user=self.account)

    def test_public_view_get(self):
        request = self.factory.get('/api/v1/users/')
        force_authenticate(request, user=self.account, token=self.token)
        view = PublicUserViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_me_view_get(self):
        request = self.factory.get('/api/v1/users/me/')
        force_authenticate(request, user=self.account, token=self.token)
        view = UserViewSet.as_view({'get': 'me'})
        response = view(request)
        response.render()
        self.assertIsInstance(response.data, OrderedDict)
        self.assertEqual(response.data['id'], self.account.id)


class RegistrationViewCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # self.client = APIClient()

    def test_registration_empty(self):
        request = self.factory.post('/api/v1/registration/')

        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        self.assertEqual(response.status_code, 400)

    def test_registration_wrong_fields(self):
        request = self.factory.post('/api/v1/registration/', {'foo': 'bar'})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        self.assertEqual(response.status_code, 400)

    def test_registration_wrong_phone(self):
        request = self.factory.post('/api/v1/registration/', {'phone': '999'})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        self.assertEqual(response.status_code, 400)

    def test_registration_right_phone(self):
        phone_number = '9999999999'
        request = self.factory.post('/api/v1/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('phone'), phone_number)

    def test_registration_wrong_code(self):
        phone_number = '9998887771'
        request = self.factory.post('/api/v1/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        code = PhoneCode.objects.filter(is_confirmed=False, phone=phone_number).first()

        self.assertIsNotNone(code)
        self.assertTrue(code.is_active())
        request_code = self.factory.post('/api/v1/registration/', {'phone': phone_number, 'code': '000000'})
        response_code = view(request_code)
        response_code.render()
        self.assertEqual(response_code.status_code, 400)

    def test_registration_wrong_phone_with_code(self):
        phone_number = '9998887772'
        request = self.factory.post('/api/v1/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        code = PhoneCode.objects.filter(is_confirmed=False, phone=phone_number).first()

        self.assertIsNotNone(code)
        self.assertTrue(code.is_active())
        request_code = self.factory.post('/api/v1/registration/', {'phone': '111', 'code': code.code})
        response_code = view(request_code)
        response_code.render()
        self.assertEqual(response_code.status_code, 400)

    def test_registration_flow(self):
        phone_number = '79998887773'
        request = self.factory.post('/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        code = PhoneCode.objects.filter(is_confirmed=False, phone=phone_number).first()

        request_code = self.factory.post('/api/v1/registration/', {'phone': code.phone, 'code': code.code})
        response_code = view(request_code)
        response_code.render()
        self.assertIsNotNone(response_code.data.get('hash'))
        self.assertEqual(response_code.data.get('phone'), phone_number)

        client_reg = self.client.post('/api/v1/registration/', {
            'phone': response_code.data.get('phone'),
            'hash': response_code.data.get('hash'),
            'username': 'Петя I23edd  34 34vd3  3',
            'password': '23456',
            'password_again': '23456'
        })
        self.assertEqual(client_reg.status_code, 200)
        self.assertIsNotNone(client_reg.data.get('user').get('token'))

    def test_registration_flow_wrong_name(self):
        phone_number = '79998887774'
        request = self.factory.post('/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        code = PhoneCode.objects.filter(is_confirmed=False, phone=phone_number).first()

        request_code = self.factory.post('/api/v1/registration/', {'phone': code.phone, 'code': code.code})
        response_code = view(request_code)
        response_code.render()
        self.assertIsNotNone(response_code.data.get('hash'))
        self.assertEqual(response_code.data.get('phone'), phone_number)

        client_reg = self.client.post('/api/v1/registration/', {
            'phone': response_code.data.get('phone'),
            'hash': response_code.data.get('hash'),
            'username': 'A\        B',
            'password': '23456',
            'password_again': '23456'
        })
        self.assertEqual(client_reg.status_code, 400)

    def test_registration_flow_wrong_password(self):
        phone_number = '79998887'
        request = self.factory.post('/registration/', {'phone': phone_number})
        view = RegistrationView.as_view()
        response = view(request)
        response.render()
        code = PhoneCode.objects.filter(is_confirmed=False, phone=phone_number).first()

        request_code = self.factory.post('/api/v1/registration/', {'phone': code.phone, 'code': code.code})
        response_code = view(request_code)
        response_code.render()
        self.assertIsNotNone(response_code.data.get('hash'))
        self.assertEqual(response_code.data.get('phone'), phone_number)

        client_reg = self.client.post('/api/v1/registration/', {
            'phone': response_code.data.get('phone'),
            'hash': response_code.data.get('hash'),
            'username': 'MK         ',
            'password': '23   456',
            'password_again': '23457'
        })
        self.assertEqual(client_reg.status_code, 400)

        client_reg = self.client.post('/api/v1/registration/', {
            'phone': response_code.data.get('phone'),
            'hash': response_code.data.get('hash'),
            'username': 'MK         ',
            'password': '23',
            'password_again': '23'
        })
        self.assertEqual(client_reg.status_code, 400)

        client_reg = self.client.post('/api/v1/registration/', {
            'phone': response_code.data.get('phone'),
            'hash': response_code.data.get('hash'),
            'username': 'MK         ',
            'password': '2     3',
            'password_again': '2     3',
        })
        self.assertEqual(client_reg.status_code, 400)


class NicknamesTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.account = User.objects.create(
            username='test',
            first_name='Иван',
            last_name='Петров',
            avatar='/tmp/avatar.jpg',
            social='vk',
            uid='12345'
        )
        self.token = Token.objects.create(user=self.account)

    def test_nickname_change(self):
        print 'good'
        print self.account.nickname
