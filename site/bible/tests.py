from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from bible.api.BiblePassageView import BiblePassageView
from bible.sources import PassageNotFoundException


class BiblePassageViewTests(SimpleTestCase):
    def test_missing_passage_is_a_404(self):
        request = APIRequestFactory().get("/api/v1/bible/Nowhere%201:1/esv")
        with patch("bible.api.BiblePassageView.Passage", side_effect=PassageNotFoundException):
            response = BiblePassageView.as_view()(request, passage="Nowhere%201:1", version="esv")
        self.assertEqual(response.status_code, 404)
