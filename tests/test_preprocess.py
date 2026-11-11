"""Exercise the CSV interface and the data contract with synthetic rows."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.preprocess import OUTPUT_COLUMNS, build, read_source


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "uniq_id", "pid", "product_url", "product_name", "product_category_tree", "brand",
    "discounted_price", "retail_price", "description", "product_specifications", "crawl_timestamp",
]
ROUTERS = "Computers >> Network Components >> Routers"
SPECIFICATIONS = '{"product_specification"=>[{"key"=>"Wireless Speed","value"=>"300 Mbps"},{"key"=>"Ports","value"=>"Four Ethernet ports"}]}'


def fixture(identifier, category=ROUTERS, **overrides):
    return {
        "uniq_id": identifier,
        "pid": f"pid-{identifier}",
        "product_url": f"https://example.invalid/product/{identifier}",
        "product_name": f"Example Router {identifier}",
        "product_category_tree": json.dumps([category]),
        "brand": "  Example   Brand  ",
        "discounted_price": "₹1,499.50",
        "retail_price": "1999",
        "description": "Dual band wireless connectivity and four Ethernet ports for wired devices.",
        "product_specifications": SPECIFICATIONS,
        "crawl_timestamp": "2016-03-01 00:00:00 +0000",
        **overrides,
    }


class PreprocessTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.input = self.directory / "source.csv"
        self.output = self.directory / "processed" / "electronics.csv"
        self.report = self.directory / "processed" / "data_quality.json"

    def write_source(self, rows):
        with self.input.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def run_build(self, *rows):
        self.write_source(rows)
        report = build(self.input, self.output, self.report)
        return pd.read_csv(self.output, keep_default_na=False), report

    def test_stable_unique_ids_and_source_trace(self):
        first, second = fixture("aaaa"), fixture("zzzz")
        frame, _ = self.run_build(second, first)
        self.assertEqual(frame.product_id.tolist(), ["P-aaaa", "P-zzzz"])
        self.assertTrue(frame.product_id.is_unique)
        self.assertEqual(frame.loc[0, "source_ref"], "kaggle:PromptCloudHQ/flipkart-products/v1#uniq_id=aaaa")
        self.assertEqual(frame.loc[0, "source_row"], 2)
        self.assertEqual(frame.loc[0, "source_url"], first["product_url"])
        reordered, _ = self.run_build(first, second)
        self.assertEqual(reordered.product_id.tolist(), frame.product_id.tolist())
        self.assertEqual(reordered.loc[0, "source_row"], 1)

    def test_only_approved_category_paths_pass(self):
        frame, report = self.run_build(
            fixture("router", category=ROUTERS + " >> Example Wireless Router"),
            fixture("case", category="Mobiles & Accessories >> Tablet Accessories >> Cases & Covers"),
            fixture("lookalike", category="Clothing >> Network Components >> Routers"),
            fixture("badpath", product_category_tree="Computers >> Network Components >> Routers"),
        )
        self.assertEqual(frame.category.tolist(), ["Routers & Networking"])
        self.assertEqual(report["excluded_rows_by_reason"]["outside_category_scope"], 3)
        self.assertEqual(report["raw_unparseable_category_paths"], 1)

    def test_duplicate_source_ids_pids_and_urls(self):
        original = fixture("a")
        frame, report = self.run_build(
            fixture("d", product_url=original["product_url"]),
            fixture("c", pid=original["pid"]), original, original,
        )
        self.assertEqual(frame.product_id.tolist(), ["P-a"])
        self.assertEqual(report["raw_exact_duplicate_rows_after_first"], 1)
        self.assertEqual(report["excluded_rows_by_reason"]["duplicate_usable_record"], 3)

    def test_required_fields_and_normalized_schema(self):
        frame, report = self.run_build(
            fixture("kept", product_name="  Example\tRouter  ", brand="   A\nBrand   "),
            fixture("no-name", product_name="  "),
            fixture("no-url", product_url=""),
            fixture("", product_url="https://example.invalid/extra"),
        )
        self.assertEqual(list(frame.columns), OUTPUT_COLUMNS)
        self.assertEqual(frame.loc[0, "name"], "Example Router")
        self.assertEqual(frame.loc[0, "brand"], "A Brand")
        self.assertEqual(frame.loc[0, "specifications"], "Wireless Speed: 300 Mbps | Ports: Four Ethernet ports")
        self.assertEqual(report["excluded_rows_by_reason"]["missing_required_identity"], 3)

    def test_numeric_prices_and_unknowns(self):
        raw_prices = {"blank": "", "invalid": "contact seller", "zero": "0", "negative": "-5",
                      "bad_grouping": "12,34", "valid": "INR 1,49,999.50"}
        frame, report = self.run_build(*(fixture(key, discounted_price=value) for key, value in raw_prices.items()))
        prices = frame.set_index("source_uniq_id").price
        self.assertEqual(float(prices["valid"]), 149999.5)
        self.assertTrue(all(prices[key] == "" for key in raw_prices if key != "valid"))
        self.assertEqual(report["cleaned_missing_values"]["price"], 5)
        self.assertEqual(report["raw_nonempty_invalid_prices"]["discounted_price"], 4)

    def test_description_quality_and_specification_fallback(self):
        frame, report = self.run_build(
            fixture("boilerplate", description="Buy Example Router boilerplate for Rs.100 online. Only Genuine Products."),
            fixture("insufficient", description="Example Router insufficient", product_specifications=""),
            fixture("listing", description="Buy Example Router listing only for Rs. 5999 from Flipkart.com. Free Shipping. Cash On Delivery!", product_specifications=""),
            fixture("unparsed", product_specifications="broken but factual raw specification"),
        )
        data = frame.set_index("source_uniq_id")
        self.assertEqual(data.loc["boilerplate", "description_source"], "source_specifications")
        self.assertIn("Wireless Speed: 300 Mbps", data.loc["boilerplate", "description"])
        self.assertEqual(data.loc["unparsed", "specification_format"], "source_text")
        self.assertEqual(data.loc["unparsed", "specifications"], "broken but factual raw specification")
        self.assertEqual(report["excluded_rows_by_reason"]["insufficient_description_and_specs"], 2)

    def test_repeated_build_is_byte_identical_and_reports_scope(self):
        rows = [fixture(str(i)) for i in range(105)]
        rows.append(fixture("headphones", category="Gaming >> Gaming Accessories >> Headphones (With Mic)"))
        _, report = self.run_build(*rows)
        expected = self.output.read_bytes(), self.report.read_bytes()
        build(self.input, self.output, self.report)
        self.assertEqual((self.output.read_bytes(), self.report.read_bytes()), expected)
        self.assertEqual(report["cleaned_rows"], 101)
        self.assertEqual(report["excluded_rows_by_reason"]["curation_limit"], 5)
        self.assertFalse(report["target_minimum_met"])
        self.assertEqual(report["raw_rows"], report["cleaned_rows"] + sum(report["excluded_rows_by_reason"].values()))

    def test_empty_and_malformed_csv(self):
        malformed_inputs = [
            ("", "empty"),
            (",".join(FIELDS) + "\n", "no data"),
            ("wrong,columns\none,two\n", "missing required columns"),
            (",".join(FIELDS + ["uniq_id"]) + "\n", "duplicate column names"),
            (",".join(FIELDS) + "\nonly,two\n", "record 1 has 2 fields"),
            (",".join(FIELDS) + '\n"unterminated\n', "Malformed CSV"),
        ]
        for data, error in malformed_inputs:
            with self.subTest(error=error):
                self.input.write_text(data, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error):
                    read_source(self.input)

    def test_cli_reports_zero_coverage_without_writing_csv(self):
        self.write_source([fixture("unrelated", category="Clothing >> Shirts")])
        result = subprocess.run(
            [sys.executable, "-m", "src.preprocess", "--input", str(self.input),
             "--output", str(self.output), "--report", str(self.report)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("No usable electronics records", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(json.loads(self.report.read_text())["cleaned_rows"], 0)


if __name__ == "__main__":
    unittest.main()
