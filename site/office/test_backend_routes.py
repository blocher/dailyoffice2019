from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve

from office.api.views.index import MorningPrayerView
from standrew.models import BibleStudyDay


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class BackendRouteTests(TestCase):
    def assert_json_not_found(self, path):
        response = self.client.get(path, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_unknown_url_returns_json_without_rendering_templates(self):
        with patch("office.views.render", side_effect=AssertionError("404 must not render HTML")):
            self.assert_json_not_found("/unknown-page/")

    def test_view_raised_http404_returns_json(self):
        self.assert_json_not_found("/bible_study/00000000-0000-0000-0000-000000000000")

    def test_legacy_prayer_display_routes_are_unregistered(self):
        for prayer in ("morning_prayer", "noonday_prayer", "midday_prayer", "evening_prayer", "compline"):
            for suffix in ("", "/"):
                path = f"/new/office/{prayer}/2026-10-11{suffix}"
                with self.subTest(path=path):
                    with self.assertRaises(Resolver404):
                        resolve(path)
                    self.assert_json_not_found(path)

    def test_json_morning_prayer_route_is_preserved(self):
        self.assertIs(resolve("/api/v1/office/morning_prayer/2026-10-11").func.view_class, MorningPrayerView)

    def test_patrons_page_keeps_standalone_styles(self):
        response = self.client.get("/patrons/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<style>")
        self.assertNotContains(response, "/static/office/js/bundle.")

    def test_bible_study_page_keeps_its_standalone_assets(self):
        day = BibleStudyDay.objects.create(date=date(2026, 10, 11), passage_title="A preserved study")
        for path in ("/bible_study", f"/bible_study/{day.uuid}"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "A preserved study")
                self.assertContains(response, "webawesome.loader.js")

    def test_email_preview_keeps_python_template_and_http_mjml_rendering(self):
        module = SimpleNamespace(subjects=["Preview"], render=lambda: "Preserved email content")
        # Replace only external compilation; exercise the actual Django template inheritance.
        with (
            patch("standrew.views.weekly_email", return_value=[module]),
            patch("mjml.templatetags.mjml.mjml_render", side_effect=lambda source: source) as compile_mjml,
        ):
            response = self.client.get("/email")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preserved email content")
        compile_mjml.assert_called_once()
        self.assertIn("<mjml>", compile_mjml.call_args.args[0])

    def test_word_download_remains_a_valid_document(self):
        with patch("office.views.readings_data", return_value={}):
            response = self.client.get("/readings_doc/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        self.assertIn("attachment;", response["Content-Disposition"])
        with ZipFile(BytesIO(response.content)) as document:
            self.assertIn("word/document.xml", document.namelist())

    def test_api_documentation_remains_available(self):
        for path in ("/api/", "/api/redoc/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "/static/office/js/bundle.")

    def test_admin_and_editor_assets_remain_available_to_collectstatic(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/admin/css/base.css")
        self.assertIsNotNone(finders.find("admin/css/base.css"))
        self.assertIsNotNone(finders.find("django_ckeditor_5/dist/bundle.js"))
