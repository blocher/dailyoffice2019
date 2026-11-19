from django.test import TestCase, override_settings

from psalter.models import Psalm


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class PsalmDetailApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.psalm = Psalm.objects.create(number=23)

    def test_by_number(self):
        response = self.client.get("/api/v1/psalms/23/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["number"], 23)

    def test_by_uuid(self):
        response = self.client.get(f"/api/v1/psalms/{self.psalm.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["number"], 23)

    def test_non_numeric_id_is_not_found_rather_than_server_error(self):
        # BugSnag 6afe3ba68f6b33f6cceb6f0a: /psalms/null/ raised ValueError (500).
        for value in ("null", "undefined", "abc", "1.5"):
            with self.subTest(value=value):
                self.assertEqual(self.client.get(f"/api/v1/psalms/{value}/").status_code, 404)

    def test_unknown_number_is_not_found(self):
        self.assertEqual(self.client.get("/api/v1/psalms/999/").status_code, 404)
