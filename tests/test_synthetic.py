"""The synthetic demo records must stay clearly labelled and separate from the real catalogue."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import settings  # noqa: E402
from src.chunking import chunk_product, is_synthetic, load_products  # noqa: E402
from src.prompts import SYSTEM_PROMPT  # noqa: E402


class SyntheticRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = load_products(settings.SYNTHETIC_CSV)

    def test_every_record_is_labelled(self):
        self.assertGreaterEqual(len(self.products), 10)
        for p in self.products:
            with self.subTest(p=p.product_id):
                self.assertTrue(p.product_id.startswith("S-"))
                self.assertTrue(is_synthetic(p))
                self.assertEqual(p.description_source, "synthetic")
                self.assertIsNotNone(p.price)

    def test_label_reaches_every_chunk(self):
        for p in self.products:
            for c in chunk_product(p):
                self.assertIn("SYNTHETIC", c.text)
                self.assertEqual(c.metadata["source_ref"], "SYNTHETIC")

    def test_prompt_tells_the_model_to_disclose_them(self):
        self.assertIn("SYNTHETIC", SYSTEM_PROMPT)

    @unittest.skipUnless(settings.PROCESSED_CSV.is_file(), "needs data/processed/electronics.csv")
    def test_no_id_clash_with_the_real_catalogue(self):
        real = {p.product_id for p in load_products(settings.PROCESSED_CSV)}
        self.assertFalse(real & {p.product_id for p in self.products})
        self.assertFalse(any(is_synthetic(p) for p in load_products(settings.PROCESSED_CSV)))


if __name__ == "__main__":
    unittest.main()
