from django.test import TestCase
from rest_framework.test import APIRequestFactory, APIClient, RequestsClient

from accounts.auth import jwt_decode
from accounts.models import User


class JWTAuthTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.api_client = APIClient()
        self.requests_client = RequestsClient()
        self.user = User.objects.create(username='user1234567890', first_name="John", last_name="Wick")
        self.payload = {
            "sub": self.user.username,
            "first_name": "John",
            "last_name": "Wick"
        }
        self.jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzNDU2Nzg5MCIsImZpcnN0X25hbWUiOiJKb2huIiwibGFzdF9uYW1lIjoiV2ljayJ9.EA4z2i0wXsF_jcWn5DMSI9RD4C7Sq4J9HOjxK0NRlxkA3NrrN-yH9tnHgMdLYB1hyb3P0yHO5hQj1PlBAF6IWYJHl85cuwtlm7T4_TTAwo66NIbG7zR5LKes0c6_FbKDvV5_6nXuej9PIitgtW3s55o2LBKSKOmLodO_O5XkPLxr5dADzrVpQKWwqYGwWaswTY-QwdRdwKUQr7SIafKxFyXM5yLiDpDwbFQv4TQAtSYQ7aw-G_3rNuoLCpBbb4wsoddNery1to-IgPwmRw19G3Y-mCtxB9D-uz3DM8z0mGihb7N4RJmSDOHKwZSUIFhtyPwVXccAPzBjmld_eSA1Vw"

    def test_jwt_decode(self):
        err, payload = jwt_decode(self.jwt)
        self.assertIsNone(err)
        self.assertIsInstance(payload, dict)

    def test_jwt_authorization(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.jwt)
        response = client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 200)

        self.user.is_active = False
        self.user.save()

        response = client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 403)
