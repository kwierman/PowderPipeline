"""
Tests for ski_pass_scraper.

Run with:  pytest tests/
"""

import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ski_pass_scraper.fallback_data import IKON_RESORTS, EPIC_RESORTS, get_all_fallback_resorts
from ski_pass_scraper.geocoder import geocode_resort, COORD_CACHE
from ski_pass_scraper.pipeline import run, _deduplicate


# ── fallback_data ──────────────────────────────────────────────────────────

class TestFallbackData:
    def test_ikon_resorts_non_empty(self):
        assert len(IKON_RESORTS) >= 20

    def test_epic_resorts_non_empty(self):
        assert len(EPIC_RESORTS) >= 20

    def test_all_ikon_have_required_keys(self):
        for r in IKON_RESORTS:
            assert "name" in r and "region" in r and "country" in r

    def test_all_epic_have_required_keys(self):
        for r in EPIC_RESORTS:
            assert "name" in r and "region" in r and "country" in r

    def test_get_all_fallback_has_pass_name(self):
        all_resorts = get_all_fallback_resorts()
        for r in all_resorts:
            assert r["pass_name"] in ("Ikon Pass", "Epic Pass")

    def test_no_empty_names(self):
        for r in IKON_RESORTS + EPIC_RESORTS:
            assert r["name"].strip(), f"Empty name found: {r}"


# ── geocoder ──────────────────────────────────────────────────────────────

class TestGeocoder:
    def test_cache_hit_exact(self):
        lat, lon = geocode_resort("Vail Mountain")
        assert lat is not None and lon is not None
        assert 39.0 < lat < 40.5
        assert -107.0 < lon < -105.5

    def test_cache_hit_partial(self):
        lat, lon = geocode_resort("Whistler Blackcomb")
        assert lat is not None

    def test_unknown_resort_returns_none_without_network(self):
        # Patch Nominatim to always fail
        with patch("ski_pass_scraper.geocoder._nominatim_query", return_value=None):
            lat, lon = geocode_resort("XYZ Totally Fake Ski Resort 99999")
        assert lat is None and lon is None


# ── pipeline._deduplicate ─────────────────────────────────────────────────

class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        data = [
            {"name": "Vail Mountain", "pass_name": "Epic Pass"},
            {"name": "Vail Mountain", "pass_name": "Epic Pass"},
        ]
        result = _deduplicate(data)
        assert len(result) == 1

    def test_keeps_same_resort_on_different_passes(self):
        data = [
            {"name": "Chamonix", "pass_name": "Ikon Pass"},
            {"name": "Chamonix", "pass_name": "Epic Pass"},
        ]
        result = _deduplicate(data)
        assert len(result) == 2

    def test_case_insensitive(self):
        data = [
            {"name": "VAIL MOUNTAIN", "pass_name": "Epic Pass"},
            {"name": "vail mountain", "pass_name": "Epic Pass"},
        ]
        result = _deduplicate(data)
        assert len(result) == 1


# ── pipeline.run (integration) ─────────────────────────────────────────────

class TestPipelineRun:
    def test_fallback_produces_csv(self, tmp_path):
        out_file = tmp_path / "test_resorts.csv"
        result = run(
            output_path=str(out_file),
            use_fallback=True,
            geocode=False,
        )
        assert result.exists()
        with open(result, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 40
        for row in rows:
            assert row["resort_name"]
            assert row["pass_name"] in ("Ikon Pass", "Epic Pass")

    def test_csv_has_correct_headers(self, tmp_path):
        out_file = tmp_path / "headers.csv"
        run(output_path=str(out_file), use_fallback=True, geocode=False)
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == {
                "resort_name", "pass_name", "region", "country", "latitude", "longitude"
            }

    def test_known_resorts_have_coordinates(self, tmp_path):
        out_file = tmp_path / "coords.csv"
        run(output_path=str(out_file), use_fallback=True, geocode=False)
        with open(out_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {r["resort_name"]: r for r in reader}

        # Vail should have coordinates from the cache
        assert rows["Vail Mountain"]["latitude"] != ""
        assert rows["Vail Mountain"]["longitude"] != ""

    def test_scraper_fallback_triggered_on_empty_scrape(self, tmp_path):
        """If scrapers return empty lists, pipeline uses fallback."""
        out_file = tmp_path / "fallback.csv"
        with patch("ski_pass_scraper.pipeline.scrape_ikon_resorts", return_value=[]), \
             patch("ski_pass_scraper.pipeline.scrape_epic_resorts", return_value=[]):
            run(output_path=str(out_file), use_fallback=False, geocode=False)

        with open(out_file, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 40   # fallback data loaded
