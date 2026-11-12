"""Index build, idempotent rebuilds, metadata round-trip and filtered retrieval.

These tests use a real persistent ChromaDB in a temporary directory with a small
deterministic hashing embedder, so they need no model download or network. The
real-model test at the bottom runs only when ``RUN_MODEL_TESTS=1`` and a built
index exists.
"""

import csv
import hashlib
import math
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import chromadb  # noqa: F401
    HAVE_CHROMA = True
except ImportError:  # pragma: no cover
    HAVE_CHROMA = False

from src import settings  # noqa: E402
from src.retrieval import build_where  # noqa: E402

FIELDS = ["product_id", "name", "category", "brand", "price", "description", "specifications",
          "source_ref", "source_uniq_id", "source_pid", "source_url", "source_row", "source_category",
          "crawl_timestamp", "retail_price", "description_source", "specification_format"]

CATALOGUE = [
    ("r1", "TP-Link Wireless Router", "Routers & Networking", "1299", "Dual band wifi router with Ethernet ports and wide wireless coverage for home networking."),
    ("r2", "D-Link Wifi Range Extender", "Routers & Networking", "", "Wireless range extender repeater that boosts wifi signal coverage."),
    ("h1", "Sony Bass Headphones", "Headphones & Earphones", "1990", "Over ear headphones with deep bass sound and a comfortable headband."),
    ("h2", "Boat Bluetooth Earphones", "Headphones & Earphones", "899", "Wireless bluetooth earphones with mic and long battery for music calls."),
    ("s1", "JBL Portable Speaker", "Speakers", "2999", "Portable bluetooth speaker with loud sound and bass for parties."),
    ("c1", "Samsung Fast Mobile Charger", "Chargers & Adapters", "599", "Fast charging wall charger adapter with USB cable for mobile phones."),
    ("l1", "Lenovo Student Laptop", "Laptops", "24990", "Laptop notebook computer for students with Intel processor, RAM and storage for study."),
    ("long", "Long Description Power Bank", "Power Banks", "1499",
     " ".join(f"Power bank feature {i} gives portable charging capacity for phones." for i in range(60))),
]


class HashingEmbedder:
    """Deterministic bag-of-words embedder used only for tests."""

    model_name = "test-hashing-embedder"
    dimension = 256

    def _vector(self, text):
        vector = [0.0] * self.dimension
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            vector[int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimension] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts):
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        return self._vector(text)


def write_catalogue(path, rows=CATALOGUE):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for index, (ident, name, category, price, description) in enumerate(rows, start=1):
            writer.writerow({f: "" for f in FIELDS} | {
                "product_id": f"P-{ident}", "name": name, "category": category, "brand": name.split()[0],
                "price": price, "description": description, "specifications": f"Model: {ident.upper()}",
                "source_ref": f"kaggle:PromptCloudHQ/flipkart-products/v1#uniq_id={ident}",
                "source_uniq_id": ident, "source_url": f"https://example.invalid/{ident}",
                "source_row": str(index), "description_source": "source_description",
            })


class BuildWhereTests(unittest.TestCase):
    def test_no_filter(self):
        self.assertIsNone(build_where())

    def test_price_filter_requires_known_price(self):
        self.assertEqual(build_where(max_price=2000), {"$and": [{"price_known": {"$eq": True}}, {"price": {"$lte": 2000.0}}]})

    def test_category_only(self):
        self.assertEqual(build_where(categories=["Speakers"]), {"category": {"$eq": "Speakers"}})


@unittest.skipUnless(HAVE_CHROMA, "chromadb is not installed")
class IndexAndRetrievalTests(unittest.TestCase):
    def setUp(self):
        from scripts.build_index import build_index
        from src.retrieval import Retriever
        from src.vector_store import open_collection

        temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.csv = self.dir / "electronics.csv"
        self.index = self.dir / "chroma"
        write_catalogue(self.csv)
        self.embedder = HashingEmbedder()
        self.build = lambda **kw: build_index(self.csv, self.index, "test_collection", embedder=self.embedder, **kw)
        self.manifest = self.build()
        self.collection = open_collection(self.index, "test_collection", self.embedder.model_name)
        self.retriever = Retriever(collection=self.collection, embedder=self.embedder)

    def test_manifest_records_build_configuration(self):
        m = self.manifest
        self.assertEqual(m["products"], len(CATALOGUE))
        self.assertGreater(m["chunks"], len(CATALOGUE))  # the long record is split
        self.assertEqual(m["products_split_into_multiple_chunks"], 1)
        self.assertEqual(m["embedding_model"], "test-hashing-embedder")
        self.assertEqual(m["chunk_settings"], {"max_record_chars": 800, "size": 700, "overlap": 75})
        self.assertEqual(len(m["input_sha256"]), 64)
        self.assertTrue((self.index / settings.MANIFEST_NAME).is_file())

    def test_repeated_ingestion_creates_no_duplicates(self):
        first = self.collection.count()
        second = self.build()
        self.assertEqual(second["sync"]["new"], 0)
        self.assertEqual(second["sync"]["stored"], first)
        ids = self.collection.get(include=[])["ids"]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rebuild_removes_stale_chunks(self):
        write_catalogue(self.csv, CATALOGUE[:3])
        manifest = self.build()
        self.assertEqual(manifest["sync"]["stored"], 3)
        self.assertGreater(manifest["sync"]["deleted_stale"], 0)

    def test_reset_rebuild(self):
        manifest = self.build(reset=True)
        self.assertEqual(manifest["sync"]["new"], manifest["chunks"])

    def test_semantic_search_returns_identity_and_source(self):
        results = self.retriever.search("wifi router for home networking", k=3)
        self.assertEqual(results[0].product_id, "P-r1")
        top = results[0]
        self.assertEqual((top.name, top.category, top.price), ("TP-Link Wireless Router", "Routers & Networking", 1299.0))
        self.assertEqual(top.source_ref, "kaggle:PromptCloudHQ/flipkart-products/v1#uniq_id=r1")
        self.assertIn("Product ID: P-r1", top.text)
        self.assertEqual([r.rank for r in results], [1, 2, 3])

    def test_default_returns_five_unique_products(self):
        results = self.retriever.search("portable charging power bank phones", k=5)
        self.assertEqual(len(results), 5)
        self.assertEqual(len({r.product_id for r in results}), 5)
        self.assertEqual(results[0].product_id, "P-long")

    def test_all_chunks_mode_can_return_several_chunks_of_one_product(self):
        results = self.retriever.search("power bank feature portable charging", k=5, unique_products=False)
        self.assertGreater(sum(r.product_id == "P-long" for r in results), 1)

    def test_budget_filter_excludes_expensive_and_unknown_prices(self):
        results = self.retriever.search("wireless wifi range extender", k=8, max_price=1500)
        self.assertTrue(results)
        self.assertTrue(all(r.price is not None and r.price <= 1500 for r in results))
        self.assertNotIn("P-r2", [r.product_id for r in results])  # unknown price never meets a budget

    def test_category_filter(self):
        results = self.retriever.search("bass sound", k=5, categories=["Speakers"])
        self.assertEqual([r.product_id for r in results], ["P-s1"])

    def test_unknown_price_is_none_not_zero(self):
        results = self.retriever.search("range extender repeater", k=1)
        self.assertEqual(results[0].product_id, "P-r2")
        self.assertIsNone(results[0].price)

    def test_model_mismatch_is_rejected(self):
        from src.vector_store import IndexNotReadyError, open_collection
        with self.assertRaises(IndexNotReadyError):
            open_collection(self.index, "test_collection", settings.EMBEDDING_MODEL)

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            self.retriever.search("   ")


@unittest.skipUnless(os.environ.get("RUN_MODEL_TESTS") == "1", "set RUN_MODEL_TESTS=1 after building the real index")
class RealIndexTests(unittest.TestCase):
    """Acceptance checks against the real catalogue index and all-MiniLM-L6-v2."""

    @classmethod
    def setUpClass(cls):
        from src.retrieval import Retriever
        cls.retriever = Retriever()

    def assert_category(self, query, category, minimum=3):
        results = self.retriever.search(query, k=5)
        self.assertEqual(len(results), 5)
        hits = sum(r.category == category for r in results)
        self.assertGreaterEqual(hits, minimum, [(r.name, r.category) for r in results])
        for r in results:
            self.assertTrue(r.product_id.startswith("P-") and r.source_ref.startswith("kaggle:"))
            self.assertIn(f"Product ID: {r.product_id}", r.text)

    def test_router_query(self):
        self.assert_category("wifi router for home internet", "Routers & Networking")

    def test_headphone_query(self):
        self.assert_category("headphones with mic for calls", "Headphones & Earphones")

    def test_speaker_query(self):
        # The catalogue has one Bluetooth speaker; it must rank first. Home theatres also
        # match "bluetooth speaker", so only two of five are speakers (failure case F1 in
        # docs/phase2_build_log.md). This guards the observed behaviour against regressions.
        results = self.retriever.search("portable bluetooth speaker", k=5)
        self.assertEqual(results[0].category, "Speakers")
        self.assertIn("Bluetooth", results[0].name)
        self.assertGreaterEqual(sum(r.category == "Speakers" for r in results), 2)

    def test_charging_query(self):
        self.assert_category("fast mobile phone charger", "Chargers & Adapters")

    def test_laptop_for_students(self):
        results = self.retriever.search("laptop for students", k=5)
        self.assertIn("Laptops", [r.category for r in results])

    def test_budget_query(self):
        results = self.retriever.search("headphones", k=5, max_price=1000)
        self.assertTrue(results)
        self.assertTrue(all(r.price is not None and r.price <= 1000 for r in results))


if __name__ == "__main__":
    unittest.main()
