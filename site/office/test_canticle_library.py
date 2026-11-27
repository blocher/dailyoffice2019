from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from office.api.views.resources import CanticlesView
from office.canticle_library import CLASS_SLUGS, SLOTS, canticle_library


def cell(library, rotation_key, day_key, slot):
    rotation = next(rotation for rotation in library["rotations"] if rotation["key"] == rotation_key)
    row = next(row for row in rotation["rows"] if day_key in row["days"])
    return row["cells"][slot]


def canticle_for(library, rotation_key, day_key, slot, season):
    for group in cell(library, rotation_key, day_key, slot):
        if not group["seasons"] or season in group["seasons"]:
            return group["canticles"]
    raise AssertionError(f"No canticle for {rotation_key} {day_key} {slot} {season}")


class CanticleLibraryTests(SimpleTestCase):
    def setUp(self):
        self.library = canticle_library()
        self.by_slug = {entry["slug"]: entry for entry in self.library["canticles"]}

    def test_every_canticle_the_offices_use_is_listed_once(self):
        slugs = [entry["slug"] for entry in self.library["canticles"]]
        self.assertEqual(len(slugs), len(set(slugs)))
        for slug in set(CLASS_SLUGS.values()) | {"venite", "pascha-nostrum", "phos-hilaron"}:
            self.assertIn(slug, self.by_slug)

    def test_texts_in_both_styles_without_the_office_titles(self):
        for entry in self.library["canticles"]:
            for style in ("contemporary", "traditional"):
                with self.subTest(slug=entry["slug"], style=style):
                    lines = entry["texts"][style]
                    self.assertGreater(len(lines), 4)
                    self.assertNotIn(lines[0]["line_type"], {"heading", "rubric", "spacer"})
                    self.assertNotIn("citation", {line["line_type"] for line in lines})
        self.assertNotEqual(
            self.by_slug["te-deum"]["texts"]["contemporary"][0]["content"],
            self.by_slug["te-deum"]["texts"]["traditional"][0]["content"],
        )

    def test_gloria_patri_closes_the_canticles_that_take_it(self):
        magnificat = self.by_slug["magnificat"]["texts"]
        self.assertIn("Glory be to the Father", magnificat["contemporary"][-2]["content"])
        self.assertIn("Holy Ghost", magnificat["traditional"][-2]["content"])
        self.assertNotIn("Glory be to the Father", self.by_slug["te-deum"]["texts"]["contemporary"][-2]["content"])

    def test_citations_come_from_the_class_or_the_text_file(self):
        self.assertEqual(self.by_slug["benedictus"]["citation"], "Luke 1:68-79")
        self.assertEqual(self.by_slug["venite"]["citation"], "Psalm 95:1-7, 8-11")
        self.assertEqual(self.by_slug["benedictus-es-domine"]["latin_name"], "Benedictus es, Domine")

    def test_rotation_tables_follow_the_rules(self):
        lib = self.library
        # Traditional: the Te Deum, except in Lent.
        self.assertEqual(canticle_for(lib, "default", "monday", "mp1", "advent"), ["te-deum"])
        self.assertEqual(canticle_for(lib, "default", "monday", "mp1", "lent"), ["benedictus-es-domine"])
        self.assertEqual(len(next(r for r in lib["rotations"] if r["key"] == "default")["rows"]), 1)
        # Daily rotation (1979 table).
        self.assertEqual(canticle_for(lib, "1979", "monday", "mp1", "pentecost"), ["ecce-deus"])
        self.assertEqual(canticle_for(lib, "1979", "sunday", "mp1", "lent"), ["kyrie-pantokrator"])
        self.assertEqual(canticle_for(lib, "1979", "thursday", "mp2", "easter"), ["gloria-in-excelsis"])
        self.assertEqual(canticle_for(lib, "1979", "feast", "mp1", "lent"), ["benedictus"])
        # Seasonal rotation (2011): Benedicite on Saturdays after Pentecost.
        self.assertEqual(canticle_for(lib, "2011", "saturday", "mp1", "pentecost"), ["benedicite"])
        self.assertEqual(canticle_for(lib, "2011", "tuesday", "mp1", "pentecost"), ["ecce-deus"])
        self.assertEqual(canticle_for(lib, "2011", "wednesday", "ep2", "lent"), ["kyrie-pantokrator"])
        self.assertEqual(canticle_for(lib, "2011", "saturday", "ep2", "lent"), ["nunc-dimittis"])

    def test_matching_weekdays_share_a_row(self):
        rotation = next(r for r in self.library["rotations"] if r["key"] == "2011")
        row = next(row for row in rotation["rows"] if "monday" in row["days"])
        self.assertEqual(row["days"], ["monday", "tuesday", "wednesday", "thursday", "friday"])
        self.assertEqual(row["label"], "Monday – Friday")

    def test_every_appointed_slug_is_in_the_library(self):
        slots = {slot["key"] for slot in SLOTS}
        for rotation in self.library["rotations"]:
            for row in rotation["rows"]:
                self.assertEqual(set(row["cells"]), slots)
                for groups in row["cells"].values():
                    for group in groups:
                        for slug in group["canticles"]:
                            self.assertIn(slug, self.by_slug)
            for note in rotation["notes"]:
                for slug in note["canticles"]:
                    self.assertIn(slug, self.by_slug)
        for rotation in self.library["invitatory_rotations"]:
            for appointment in rotation["appointments"]:
                for slug in appointment["canticles"]:
                    self.assertIn(slug, self.by_slug)

    def test_uses_record_offices_and_rotations(self):
        self.assertEqual(self.by_slug["nunc-dimittis"]["offices"], ["evening", "compline"])
        self.assertEqual(self.by_slug["ecce-deus"]["offices"], ["morning", "evening"])
        self.assertEqual(self.by_slug["ecce-deus"]["rotations"], ["2011", "1979"])
        self.assertEqual(self.by_slug["te-deum"]["rotations"], ["default", "2011", "1979"])
        self.assertIn("invitatory", self.by_slug["venite"]["slots"])

    def test_api_route(self):
        self.assertIs(resolve("/api/v1/canticles").func.view_class, CanticlesView)
        request = APIRequestFactory().get("/api/v1/canticles")
        response = CanticlesView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["rotations"]), 3)
