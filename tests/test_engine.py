"""MSP Pure Water — engine test suite.

Run:  python3 -m unittest discover -s tests -v
 or:  python3 -m pytest tests/      (if pytest is installed)

Covers query parsing, ZIP/city resolution, the rating model, system
recommendations, data integrity, and end-to-end PDF generation.
"""
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from water_report import knowledge_base as kb
from water_report import report as report_mod

CONFIG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))


def profile_for(query):
    """Resolve a query the same way the app does, then build the profile."""
    p = kb.resolve_query(query)
    loc = {"zip": p["zip"], "city": p["city"], "address": p["address"],
           "state_abbr": p["state_abbr"], "epa_systems": []}
    return kb.build_profile(loc), p


# --------------------------------------------------------------- query parsing
class TestQueryResolution(unittest.TestCase):
    def test_zip(self):
        p = kb.resolve_query("55443")
        self.assertEqual(p["zip"], "55443")
        self.assertEqual(p["matched_by"], "zip")
        self.assertIsNone(p["error"])

    def test_zip_inside_address(self):
        p = kb.resolve_query("123 Maple St, Woodbury, MN 55125")
        self.assertEqual(p["zip"], "55125")
        self.assertEqual(p["address"], "123 Maple St, Woodbury, MN 55125")

    def test_city_exact(self):
        p = kb.resolve_query("Brooklyn Park")
        self.assertEqual(p["matched_by"], "city")
        self.assertEqual(p["city"], "Brooklyn Park")
        self.assertEqual(p["state_abbr"], "MN")

    def test_city_case_insensitive(self):
        self.assertEqual(kb.resolve_query("eden prairie")["city"], "Eden Prairie")

    def test_city_alias_st_paul(self):
        self.assertEqual(kb.resolve_query("St Paul")["city"], "Saint Paul")

    def test_city_in_address_without_zip(self):
        p = kb.resolve_query("4521 Main Street, Maple Grove, Minnesota")
        self.assertEqual(p["city"], "Maple Grove")
        self.assertIn(p["matched_by"], ("city", "city_in_text"))

    def test_longest_city_wins(self):
        # "South Saint Paul" must not be shadowed by "Saint Paul"
        self.assertEqual(kb.resolve_query("South Saint Paul")["city"], "South Saint Paul")

    def test_fuzzy_suggestions(self):
        p = kb.resolve_query("Bloomingtonn")
        self.assertEqual(p["error"], "no_match")
        self.assertIn("Bloomington", p["suggestions"])

    def test_empty(self):
        self.assertEqual(kb.resolve_query("")["error"], "empty")

    def test_all_cities_listed(self):
        cities = kb.all_cities()
        self.assertGreater(len(cities), 50)
        self.assertEqual(cities, sorted(cities))
        self.assertEqual(len(cities), len(set(cities)))
        self.assertIn("Brooklyn Park", cities)


# ----------------------------------------------------------- city resolution
class TestCityResolution(unittest.TestCase):
    def test_postal_mislabel_fixed(self):
        # 55443 postal city is "Minneapolis" but it's really Brooklyn Park
        loc = kb.apply_zip_override({"zip": "55443", "city": "Minneapolis"})
        self.assertEqual(loc["city"], "Brooklyn Park")

    def test_core_minneapolis_zip(self):
        prof, _ = profile_for("55401")
        self.assertEqual(prof["display"], "Minneapolis")
        self.assertEqual(prof["source_type"], "surface")

    def test_zip_beats_geocoded_city(self):
        loc = {"zip": "55443", "city": "Minneapolis", "state_abbr": "MN", "epa_systems": []}
        prof = kb.build_profile(loc)
        self.assertEqual(prof["display"], "Brooklyn Park")
        self.assertGreater(prof["hardness"]["gpg"], 25)

    def test_non_mn_falls_back_national(self):
        loc = {"zip": "78701", "city": "Austin", "state_abbr": "TX", "epa_systems": []}
        prof = kb.build_profile(loc)
        self.assertEqual(prof["match"], "national")

    def test_unknown_mn_zip_is_suburb_not_minneapolis(self):
        loc = {"zip": "56301", "city": None, "state_abbr": "MN", "epa_systems": []}
        prof = kb.build_profile(loc)
        self.assertNotEqual(prof["display"], "Minneapolis")


# ------------------------------------------------------------- rating model
class TestRatings(unittest.TestCase):
    def test_brooklyn_park_extremely_hard(self):
        prof, _ = profile_for("Brooklyn Park")
        self.assertGreaterEqual(prof["hardness"]["gpg"], 30)
        self.assertEqual(prof["hardness"]["label"], "Extremely Hard")
        self.assertEqual(prof["hardness_row"]["rating"], "concerning")
        self.assertEqual(prof["hardness"]["mgl"], round(prof["hardness"]["gpg"] * 17.1))

    def test_hardness_rating_bands(self):
        self.assertEqual(kb._hardness_rating(2), "normal")
        self.assertEqual(kb._hardness_rating(6), "elevated")
        self.assertEqual(kb._hardness_rating(9), "high")
        self.assertEqual(kb._hardness_rating(20), "concerning")

    def test_hardness_uses_real_units(self):
        # Hardness is the one real, measured number — it carries units.
        prof, _ = profile_for("Brooklyn Park")
        self.assertIn("gpg", prof["hardness_row"]["level"])
        self.assertIn("ppm", prof["tds_row"]["level"])
        for c in prof["concerns"]:  # honest plain-language labels, not fabricated numbers
            self.assertTrue(c["level"].strip(), f"{c['name']} has no label")

    def test_no_fabricated_iron_manganese_on_city_water(self):
        # Truthful model: city utilities treat iron/manganese — don't auto-flag them.
        for q in ("Brooklyn Park", "Lakeville", "Plymouth", "Woodbury", "Minneapolis"):
            prof, _ = profile_for(q)
            keys = {c["key"] for c in prof["concerns"]}
            self.assertNotIn("iron", keys, q)
            self.assertNotIn("manganese", keys, q)

    def test_every_row_has_safe_level(self):
        prof, _ = profile_for("Brooklyn Park")
        for r in prof["table_rows"]:
            self.assertTrue(r.get("safe"), f"{r['name']} missing safe level")

    def test_flagged_counts_hardness_and_tds(self):
        prof, _ = profile_for("Brooklyn Park")
        names = {f["name"] for f in prof["flagged"]}
        self.assertIn("Water Hardness", names)
        self.assertIn("Total Dissolved Solids (TDS)", names)

    def test_table_shows_only_treatable_problems(self):
        # We only show what our systems remove; non-hardness rows are never "Normal".
        for q in ("Brooklyn Park", "Minneapolis", "Eden Prairie", "Woodbury"):
            prof, _ = profile_for(q)
            self.assertEqual(prof["table_rows"][0]["key"], "hardness")  # hardness always first
            for r in prof["table_rows"]:
                if r["key"] != "hardness":
                    self.assertNotEqual(r["rating"], "normal",
                                        f"{q}: {r['name']} shown but rated normal")

    def test_no_inflated_grades_anywhere(self):
        # No water coming through a city plant should grade A/B+; cap is ~C+ (B- ceiling).
        allowed = {"B-", "C+", "C", "C-", "D", "F"}
        for c in kb.all_cities():
            prof, _ = profile_for(c)
            self.assertLessEqual(prof["score"], 82, f"{c} scored too high")
            self.assertIn(prof["grade"], allowed, f"{c} got grade {prof['grade']}")
            self.assertNotIn(prof["grade"], ("A", "A+", "A-", "B+", "B"))

    def test_score_in_range(self):
        for q in ("Brooklyn Park", "Minneapolis", "Eden Prairie", "55044"):
            prof, _ = profile_for(q)
            self.assertTrue(18 <= prof["score"] <= 82)


# ----------------------------------------------------- system recommendations
class TestRecommendations(unittest.TestCase):
    def test_everyone_gets_whole_home_filtration(self):
        # Current rule: city water -> Whole Home Water Filtration System for everyone,
        # regardless of hardness (dual-tank is a large-household upsell only).
        for q in ("Brooklyn Park", "Maple Grove", "Plymouth", "Minneapolis", "Eden Prairie"):
            prof, _ = profile_for(q)
            self.assertEqual(prof["recommendation"]["primary_key"], "standard_mixed_bed", q)

    def test_dual_tank_is_large_household_upsell_only(self):
        prof, _ = profile_for("Brooklyn Park")
        alt = dict(prof["recommendation"]["alternatives"])
        self.assertIn("dual_tank_city", alt)
        self.assertRegex(alt["dual_tank_city"].lower(), r"resident|bathroom")

    def test_whole_home_system_is_named_filtration_not_softener(self):
        self.assertEqual(CONFIG["systems"]["standard_mixed_bed"]["name"],
                         "Whole Home Water Filtration System")
        self.assertNotIn("softener", CONFIG["systems"]["standard_mixed_bed"]["name"].lower())

    def test_maple_grove_is_hard_not_softened(self):
        # Audit fix: Maple Grove does not soften — it's ~25 gpg.
        prof, _ = profile_for("Maple Grove")
        self.assertGreaterEqual(prof["hardness"]["gpg"], 20)

    def test_recommendation_keys_exist_in_config(self):
        for c in kb.all_cities():
            prof, _ = profile_for(c)
            rec = prof["recommendation"]
            self.assertIn(rec["primary_key"], CONFIG["systems"])
            self.assertIn(rec["ro_default"], CONFIG["drinking"])
            for k, _ in rec["alternatives"]:
                self.assertIn(k, CONFIG["systems"])


# --------------------------------------------------------------- data integrity
class TestDataIntegrity(unittest.TestCase):
    def test_template_keys_exist_in_contaminants(self):
        for tmpl in kb.MSP["concern_templates"].values():
            for entry in tmpl:
                self.assertIn(entry["key"], kb.CONTAMINANTS)
        self.assertIn(kb.MSP["pfas_entry"]["key"], kb.CONTAMINANTS)

    def test_every_contaminant_has_safe_level(self):
        for key, c in kb.CONTAMINANTS.items():
            self.assertTrue(c.get("safe_level"), f"{key} missing safe_level")

    def test_every_city_valid(self):
        valid_sources = set(kb.MSP["source_text"])
        for key, c in kb.MSP["cities"].items():
            self.assertIn(c["source_type"], valid_sources, f"{key} bad source_type")
            self.assertIsInstance(c["hardness_gpg"], (int, float))
            self.assertTrue(0 < c["hardness_gpg"] < 60)
            self.assertTrue(c.get("display"))

    def test_template_ratings_valid(self):
        for tmpl in kb.MSP["concern_templates"].values():
            for entry in tmpl:
                self.assertIn(entry["rating"], kb.RATING)

    def test_pfas_zips_map_to_pfas_cities(self):
        # Every East-metro PFAS ZIP resolves to a real city and flags PFAS
        for z in kb.MSP["east_metro_pfas_zips"][:6]:
            loc = {"zip": z, "city": None, "state_abbr": "MN", "epa_systems": []}
            prof = kb.build_profile(loc)
            self.assertTrue(prof["pfas_zone"], f"{z} should be PFAS zone")
            self.assertTrue(any(c["key"] == "pfas" for c in prof["concerns"]))

    def test_config_has_trust_and_systems(self):
        self.assertTrue(CONFIG.get("trust_badges"))
        for key in ("standard_mixed_bed", "dual_tank_city", "dual_tank_well",
                    "peroxide", "salt_free"):
            self.assertIn(key, CONFIG["systems"])
        self.assertIn("ro_tank", CONFIG["drinking"])
        self.assertIn("ro_tankless", CONFIG["drinking"])


# ------------------------------------------------------------- PDF generation
class TestPDFGeneration(unittest.TestCase):
    def _build(self, query):
        prof, parsed = profile_for(query)
        loc = {"zip": parsed["zip"], "city": prof["display"],
               "state_abbr": parsed["state_abbr"] or "MN", "address": parsed["address"]}
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "r.pdf")
            report_mod.build_report(prof, loc, CONFIG, out, "January 01, 2026")
            self.assertTrue(os.path.exists(out))
            size = os.path.getsize(out)
            self.assertGreater(size, 8000)
            pages = None
            try:
                import fitz
                pages = fitz.open(out).page_count
            except Exception:
                pass
            return size, pages

    def test_pdf_brooklyn_park(self):
        size, pages = self._build("Brooklyn Park")
        if pages is not None:
            self.assertIn(pages, (5, 6))

    def test_pdf_city_search(self):
        # A city-name search (no ZIP) must still produce a valid PDF
        self._build("Waconia")

    def test_pdf_all_source_types(self):
        for q in ("Minneapolis", "Brooklyn Park", "Eden Prairie", "Bloomington"):
            self._build(q)


class TestWaterSource(unittest.TestCase):
    def test_every_city_has_a_real_source(self):
        for c in kb.all_cities():
            prof, _ = profile_for(c)
            self.assertTrue(prof.get("source_detail"), c)
            self.assertRegex(prof["source_detail"].lower(),
                             r"river|aquifer|well|groundwater|surface", c)

    def test_minneapolis_source_is_the_river(self):
        self.assertIn("Mississippi", profile_for("Minneapolis")[0]["source_detail"])

    def test_groundwater_city_names_the_aquifer(self):
        self.assertIn("aquifer", profile_for("Brooklyn Park")[0]["source_detail"].lower())

    def test_audit_crystal_newhope_on_soft_minneapolis_water(self):
        for c in ("Crystal", "New Hope"):
            prof, _ = profile_for(c)
            self.assertLessEqual(prof["hardness"]["gpg"], 7, c)
            self.assertIn("Minneapolis", prof["source_detail"], c)

    def test_audit_richfield_is_own_wells_not_minneapolis(self):
        prof, _ = profile_for("Richfield")
        self.assertEqual(prof["source_type"], "groundwater")
        self.assertGreater(prof["hardness"]["gpg"], 10)
        self.assertIn("well", prof["source_detail"].lower())

    def test_audit_sprws_suburbs_are_surface_water(self):
        for c in ("West Saint Paul", "Mendota Heights", "Little Canada", "Arden Hills"):
            prof, _ = profile_for(c)
            self.assertEqual(prof["source_type"], "surface", c)
            self.assertIn("Regional Water", prof["source_detail"], c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
