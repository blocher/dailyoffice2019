from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from office.api.views.index import EmailSignupView


class EmailSignupMethodTests(SimpleTestCase):
    def test_get_and_head_return_method_not_allowed(self):
        factory = APIRequestFactory()
        for method in (factory.get, factory.head):
            with self.subTest(method=method.__name__):
                response = EmailSignupView.as_view()(method("/api/v1/email_signup"))
                self.assertEqual(response.status_code, 405)
                self.assertNotIn("GET", response["Allow"])
                self.assertIn("POST", response["Allow"])

    def test_non_office_endpoint_does_not_apply_audio_date_validation(self):
        request = APIRequestFactory().get("/api/v1/email_signup", {"include_audio_links": "1"})
        self.assertEqual(EmailSignupView.as_view()(request).status_code, 405)

    def test_post_validation_and_subscription_remain_available(self):
        factory = APIRequestFactory()
        response = EmailSignupView.as_view()(factory.post("/api/v1/email_signup", {}, format="json"))
        self.assertEqual(response.status_code, 400)
        with (
            patch("office.api.views.index.MailchimpMarketing.Client") as client,
            patch("office.api.views.index.get_client_ip", return_value="192.0.2.1"),
        ):
            response = EmailSignupView.as_view()(
                factory.post("/api/v1/email_signup", {"email": "reader@example.com"}, format="json")
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        client.return_value.lists.set_list_member.assert_called_once()
