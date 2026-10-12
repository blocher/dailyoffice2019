import uuid

from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory

from churchcal.models import Calendar, Commemoration, CommemorationRank, SanctoraleCommemoration
from office.api.views.index import CommemorationsView


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class CommemorationEndpointTests(TestCase):
    def test_missing_well_formed_ids_return_not_found(self):
        for identifier in (uuid.UUID(int=0), uuid.uuid4()):
            with self.subTest(identifier=identifier):
                path = f"/api/v1/commemorations/{identifier}"
                match = resolve(path)
                self.assertIs(match.func.view_class, CommemorationsView)
                request = APIRequestFactory().get(path, HTTP_ACCEPT="application/json")
                response = match.func(request, **match.kwargs)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.data["detail"].code, "not_found")
                response.render()
                self.assertEqual(response["Content-Type"], "application/json")

    def test_malformed_ids_are_rejected_by_the_route(self):
        for identifier in ("not-a-uuid", "00000000-0000-0000-0000-00000000000g"):
            with self.subTest(identifier=identifier):
                path = f"/api/v1/commemorations/{identifier}"
                with self.assertRaises(Resolver404):
                    resolve(path)
                response = self.client.get(path, HTTP_ACCEPT="application/json")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": "Not found."})

    def make_commemoration(self, model=Commemoration, **fields):
        calendar = Calendar.objects.create(name="Synthetic calendar", year="2026")
        rank = CommemorationRank.objects.create(
            name="Synthetic rank", formatted_name="Synthetic rank", precedence_rank=5, calendar=calendar
        )
        return model.objects.create(
            name="Synthetic commemoration",
            calendar=calendar,
            rank=rank,
            color="White",
            biography="<p>Synthetic biography.</p>",
            link_1="https://example.invalid/commemoration",
            **fields,
        )

    def assert_valid_response(self, commemoration):
        response = self.client.get(f"/api/v1/commemorations/{commemoration.uuid}", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["uuid"], str(commemoration.uuid))
        self.assertEqual(data["name"], "Synthetic commemoration")
        self.assertEqual(data["rank"], {"name": "Synthetic rank", "formatted_name": "Synthetic rank", "precedence": 5})
        self.assertEqual(data["colors"], ["white"])
        self.assertEqual(data["biography"], "<p>Synthetic biography.</p>")
        self.assertEqual(data["links"], ["https://example.invalid/commemoration"])
        return data

    def test_existing_commemoration_preserves_response(self):
        data = self.assert_valid_response(self.make_commemoration())
        self.assertIsNone(data["date_string"])

    def test_existing_subclass_preserves_specific_fields(self):
        commemoration = self.make_commemoration(
            SanctoraleCommemoration, month=10, day=12, saint_name="Synthetic saint"
        )
        data = self.assert_valid_response(commemoration)
        self.assertEqual(data["date_string"], "October 12")
        self.assertEqual(data["saint_name"], "Synthetic saint")
