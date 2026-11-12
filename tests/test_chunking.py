"""Document building and chunking keep product identity attached to every chunk."""

import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.chunking import (
    Product, build_document, chunk_product, chunk_products, load_products, parse_price, split_text,
)


def product(identifier="abc", **overrides):
    base = Product(
        product_id=f"P-{identifier}", name=f"Example Router {identifier}", category="Routers & Networking",
        brand="ExampleBrand", price=1499.5, retail_price=1999.0,
        description="Dual band wireless router with four Ethernet ports for wired devices.",
        specifications="Wireless Speed: 300 Mbps | Ports: 4", description_source="source_description",
        source_ref=f"kaggle:PromptCloudHQ/flipkart-products/v1#uniq_id={identifier}",
        source_uniq_id=identifier, source_url=f"https://example.invalid/{identifier}", source_row=7,
    )
    return replace(base, **overrides)


class SplitTextTests(unittest.TestCase):
    def test_short_text_is_one_piece(self):
        self.assertEqual(split_text("short text", 700, 75), ["short text"])

    def test_windows_respect_size_and_overlap(self):
        words = " ".join(f"word{i:04d}" for i in range(400))  # ~3,600 chars
        pieces = split_text(words, 700, 75)
        self.assertGreater(len(pieces), 4)
        self.assertTrue(all(len(piece) <= 700 for piece in pieces))
        for left, right in zip(pieces, pieces[1:]):
            # The first word of the next window already appeared at the end of the previous one.
            self.assertIn(right.split()[0], left[-90:])
        # Nothing is lost: every word appears in some window.
        joined = " ".join(pieces)
        self.assertTrue(all(f"word{i:04d}" in joined for i in range(400)))

    def test_words_are_not_cut(self):
        words = " ".join(["alpha", "beta", "gamma", "delta"] * 100)
        for piece in split_text(words, 120, 20):
            for token in piece.split():
                self.assertIn(token, {"alpha", "beta", "gamma", "delta"})

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            split_text("abc", 100, 100)


class DocumentTests(unittest.TestCase):
    def test_document_contains_identity_and_evidence(self):
        text = build_document(product())
        for expected in ("Product: Example Router abc", "Product ID: P-abc", "Category: Routers & Networking",
                         "Brand: ExampleBrand", "INR 1,499.50", "Description: Dual band",
                         "Specifications: Wireless Speed: 300 Mbps"):
            self.assertIn(expected, text)

    def test_unknown_price_is_labelled_not_zero(self):
        text = build_document(product(price=None))
        self.assertIn("Historical price (2015-16 catalogue): unknown", text)
        self.assertNotIn("INR 0", text)

    def test_specs_not_repeated_when_description_came_from_specs(self):
        p = product(description="Example Router abc. Specifications: Wireless Speed: 300 Mbps | Ports: 4",
                    description_source="source_specifications")
        self.assertEqual(build_document(p).count("Wireless Speed: 300 Mbps"), 1)


class ChunkTests(unittest.TestCase):
    def test_short_record_stays_whole(self):
        chunks = chunk_product(product())
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "P-abc::chunk-00")
        self.assertEqual(chunks[0].text, build_document(product()))

    def test_long_record_is_split_and_every_chunk_keeps_identity(self):
        long_description = " ".join(f"Feature {i} improves wireless coverage." for i in range(120))
        p = product(description=long_description)
        chunks = chunk_product(p, max_record_chars=800, chunk_size=700, overlap=75)
        self.assertGreater(len(chunks), 1)
        for index, chunk in enumerate(chunks):
            self.assertEqual(chunk.chunk_id, f"P-abc::chunk-{index:02d}")
            self.assertTrue(chunk.text.startswith("Product: Example Router abc\nProduct ID: P-abc"))
            meta = chunk.metadata
            self.assertEqual((meta["product_id"], meta["name"], meta["price"]), ("P-abc", p.name, 1499.5))
            self.assertEqual(meta["source_ref"], p.source_ref)
            self.assertEqual((meta["chunk_index"], meta["chunk_count"]), (index, len(chunks)))
        self.assertIn("Specifications: Wireless Speed", chunks[-1].text)

    def test_chunk_ids_are_deterministic(self):
        first = [(c.chunk_id, c.text) for c in chunk_products([product("a"), product("b")])]
        second = [(c.chunk_id, c.text) for c in chunk_products([product("a"), product("b")])]
        self.assertEqual(first, second)

    def test_metadata_is_chroma_compatible_and_unknown_price_omitted(self):
        meta = chunk_product(product(price=None, retail_price=None))[0].metadata
        self.assertFalse(meta["price_known"])
        self.assertNotIn("price", meta)
        self.assertTrue(all(isinstance(v, (str, int, float, bool)) for v in meta.values()))


class LoadProductsTests(unittest.TestCase):
    FIELDS = ["product_id", "name", "category", "brand", "price", "description", "specifications",
              "source_ref", "source_uniq_id", "source_pid", "source_url", "source_row", "source_category",
              "crawl_timestamp", "retail_price", "description_source", "specification_format"]

    def write(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "electronics.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def row(self, identifier, **overrides):
        return {field: "" for field in self.FIELDS} | {
            "product_id": f"P-{identifier}", "name": f"Name {identifier}", "category": "Speakers",
            "price": "999.0", "description": "A portable speaker with deep bass.", "source_ref": "ref",
            "source_uniq_id": identifier, "source_url": "https://example.invalid", "source_row": "3",
            "description_source": "source_description",
        } | overrides

    def test_loads_and_parses_prices(self):
        products = load_products(self.write([self.row("a"), self.row("b", price="")]))
        self.assertEqual([p.price for p in products], [999.0, None])

    def test_rejects_duplicates_and_missing_file(self):
        with self.assertRaises(ValueError):
            load_products(self.write([self.row("a"), self.row("a")]))
        with self.assertRaises(FileNotFoundError):
            load_products(Path("does/not/exist.csv"))

    def test_parse_price(self):
        self.assertEqual(parse_price("1499.5"), 1499.5)
        for value in ("", "0", "-3", "abc", "nan", "inf"):
            self.assertIsNone(parse_price(value))


if __name__ == "__main__":
    unittest.main()
