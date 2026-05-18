from django.test import TestCase

from office.models import Scripture


class NormalizeBibleTranslationTests(TestCase):
    def test_undefined_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("undefined"), "esv")

    def test_null_and_none_strings_default_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("null"), "esv")
        self.assertEqual(Scripture.normalize_bible_translation("none"), "esv")

    def test_empty_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation(""), "esv")
        self.assertEqual(Scripture.normalize_bible_translation(None), "esv")

    def test_valid_translation_is_normalized(self):
        self.assertEqual(Scripture.normalize_bible_translation("NRSVCE"), "nrsvce")

    def test_unknown_translation_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("msg"), "esv")
