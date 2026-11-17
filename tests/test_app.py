"""Phase 4 checks for the Streamlit display helpers. No index, model or API key needed."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "scripts"))

import build_display_data  # noqa: E402
from src.retrieval import RetrievedChunk  # noqa: E402
from src.ui_helpers import (PRICE_STOPS, REASON_LABELS, cache_key, filter_summary, format_price,  # noqa: E402
                            format_rating, format_rupees, number_citations, price_stop_label, product_card_html,
                            source_numbers)


def chunk(pid, rank=1):
    return RetrievedChunk(rank=rank, score=0.5, chunk_id=f"{pid}-0", product_id=pid, name=f"Product {pid}",
                          category="Routers", brand="X", price=999.0, source_ref="ref", source_url="",
                          source_row=1, chunk_index=1, chunk_count=1, text="text")


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.sources = [chunk("P-aaa", 1), chunk("P-bbb", 2)]

    def test_numbers_follow_source_order(self):
        self.assertEqual(source_numbers(self.sources), {"P-aaa": 1, "P-bbb": 2})

    def test_duplicate_products_share_a_number(self):
        self.assertEqual(source_numbers([chunk("P-aaa"), chunk("P-aaa"), chunk("P-bbb")]), {"P-aaa": 1, "P-bbb": 2})

    def test_product_ids_become_numbers(self):
        self.assertEqual(number_citations("Buy this [P-bbb] or that [P-aaa].", self.sources),
                         "Buy this [2] or that [1].")

    def test_repeated_citations_collapse(self):
        self.assertEqual(number_citations("Cheap [P-aaa] [P-aaa].", self.sources), "Cheap [1].")

    def test_invented_ids_are_removed_other_brackets_kept(self):
        self.assertEqual(number_citations("A [P-zzz] and [note]", self.sources), "A  and [note]")


class DisplayTests(unittest.TestCase):
    def test_price_is_labelled_historical(self):
        self.assertEqual(format_price(1299.0), "INR 1,299 (2015-16 price)")

    def test_unknown_price_is_not_zero(self):
        self.assertEqual(format_price(None), "Price unknown")

    def test_rating(self):
        self.assertEqual(format_rating(4.2), "★ 4.2 / 5")
        self.assertEqual(format_rating(5.0), "★ 5 / 5")
        self.assertEqual(format_rating(None), "No rating")

    def test_card_price(self):
        self.assertEqual(format_rupees(1299.0), "₹1,299")
        self.assertEqual(format_rupees(None), "Price unknown")


class FilterDisplayTests(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(filter_summary(500.0, 2000.0, ["Mice"]), "₹500 – ₹2,000 · Mice")
        self.assertEqual(filter_summary(None, 1000.0, []), "Under ₹1,000")
        self.assertEqual(filter_summary(250.0, None, []), "Above ₹250")
        self.assertEqual(filter_summary(None, None, []), "")

    def test_price_stops(self):
        self.assertEqual(price_stop_label(PRICE_STOPS[-1]), "No limit")
        self.assertEqual(price_stop_label(5000), "₹5,000")
        self.assertEqual(PRICE_STOPS, sorted(PRICE_STOPS))


class ProductCardTests(unittest.TestCase):
    def test_card_shows_number_price_rating_and_historical_label(self):
        card = product_card_html(2, chunk("P-aaa"), "https://img/x.jpeg", 4.2)
        for part in ('class="pcard-num">2<', "₹999", "4.2 ★", 'src="https://img/x.jpeg"', "2015-16 catalogue price"):
            self.assertIn(part, card)

    def test_catalogue_text_is_escaped(self):
        c = replace(chunk("P-aaa"), name="<script>x</script>", source_url='https://a/"onmouseover="y')
        card = product_card_html(1, c, None, None)
        self.assertNotIn("<script>", card)
        self.assertNotIn('"onmouseover="', card)

    def test_card_without_link_image_or_rating(self):
        card = product_card_html(1, chunk("P-aaa"), None, None)
        self.assertNotIn("<a ", card)
        self.assertIn("No image", card)
        self.assertIn("No ratings", card)


class CacheKeyTests(unittest.TestCase):
    POWER = [{"role": "user", "content": "Suggest a power bank under 1500"}, {"role": "assistant", "content": "[P1]"}]
    ROUTER = [{"role": "user", "content": "Suggest a router"}, {"role": "assistant", "content": "[P2]"}]

    def test_same_question_ignores_case_and_punctuation(self):
        self.assertEqual(cache_key("Suggest a Router!", []), cache_key("suggest a router", []))

    def test_new_topic_ignores_history(self):
        self.assertEqual(cache_key("Suggest a router", self.POWER), cache_key("Suggest a router", []))

    def test_follow_up_depends_on_conversation(self):
        self.assertNotEqual(cache_key("which is the best?", self.POWER), cache_key("which is the best?", self.ROUTER))
        self.assertEqual(cache_key("Which is the best", self.POWER), cache_key("which is the best?", self.POWER))


class DisplayDataTests(unittest.TestCase):
    def test_image_moves_to_https_cdn(self):
        urls = '["http://img5a.flixcart.com/image/router/r/w/s/belkin.jpeg", "http://img6a.flixcart.com/x.jpeg"]'
        self.assertEqual(build_display_data.image_url(urls),
                         "https://rukminim1.flixcart.com/image/400/400/router/r/w/s/belkin.jpeg")

    def test_missing_image_and_rating(self):
        self.assertIsNone(build_display_data.image_url(None))
        self.assertIsNone(build_display_data.image_url("[]"))
        self.assertIsNone(build_display_data.rating("No rating available"))
        self.assertEqual(build_display_data.rating("4.2"), 4.2)

    def test_every_pipeline_reason_has_a_label(self):
        for reason in ("answered", "no_support", "no_evidence", "weak_evidence", "no_budget_match"):
            self.assertIn(reason, REASON_LABELS)


if __name__ == "__main__":
    unittest.main()
