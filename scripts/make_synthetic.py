"""Write the labelled synthetic records that fill the thin catalogue categories.

    python scripts/make_synthetic.py        # writes data/synthetic/synthetic_electronics.csv

The Kaggle sample has only 2 laptops, 2 mice, 4 keyboards, 3 pen drives and 5 power banks. These records
let comparison and "best for" questions work on those categories. They are INVENTED: fictional brands,
illustrative 2015-16 style prices, no real Flipkart listing behind them. Every row carries
``source_ref=SYNTHETIC`` and ``description_source=synthetic`` so the index, the prompt and the UI can label them.
Product IDs start with ``S-``. Evaluation numbers for real-catalogue claims should not rely on them.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic" / "synthetic_electronics.csv"

COLUMNS = ["product_id", "name", "category", "brand", "price", "description", "specifications", "source_ref",
           "source_uniq_id", "source_pid", "source_url", "source_row", "source_category", "crawl_timestamp",
           "retail_price", "description_source", "specification_format"]


def spec(**facts: str) -> str:
    return " | ".join(f"{k.replace('_', ' ')}: {v}" for k, v in facts.items())


# (slug, name, category, brand, price, retail_price, description, specifications)
RECORDS = [
    # ---- Laptops ----
    ("lap-01", "Veltrix Student Lite VL-14 Laptop", "Laptops", "Veltrix", 21990, 24990,
     "A light 14 inch laptop built for school and college work. It handles note taking, web research, video calls "
     "and office documents without fuss, and the battery lasts a full lecture day. The keyboard has comfortable "
     "key travel for long assignments and the matte screen is easy on the eyes. A good first laptop for a student "
     "on a budget.",
     spec(Processor="Intel Pentium Quad Core", RAM="4 GB DDR3", Storage="500 GB HDD", Screen="14 inch HD",
          Graphics="Intel HD Graphics", Operating_System="Windows 10 Home", Battery="6 hours", Weight="1.7 kg")),
    ("lap-02", "Veltrix Scholar VS-15 Laptop", "Laptops", "Veltrix", 32990, 36990,
     "A balanced 15.6 inch laptop for students who also do light photo and video editing. The Core i5 processor and "
     "8 GB of memory keep several browser tabs, a spreadsheet and a video call running together smoothly. The "
     "1 TB drive stores course material and projects, and the full size keyboard has a number pad.",
     spec(Processor="Intel Core i5 5th Gen", RAM="8 GB DDR3", Storage="1 TB HDD", Screen="15.6 inch HD",
          Graphics="Intel HD Graphics 5500", Operating_System="Windows 10 Home", Battery="5 hours", Weight="2.1 kg")),
    ("lap-03", "Nexora Titan NX-17 Gaming Laptop", "Laptops", "Nexora", 74990, 82990,
     "A powerful 17.3 inch gaming laptop for modern games and heavy creative work. The Core i7 processor and a "
     "dedicated 4 GB NVIDIA graphics card run demanding titles at high settings, and the backlit keyboard and "
     "cooling system suit long play sessions. A fast solid state drive keeps games loading quickly.",
     spec(Processor="Intel Core i7 6th Gen", RAM="16 GB DDR4", Storage="128 GB SSD + 1 TB HDD",
          Screen="17.3 inch Full HD", Graphics="NVIDIA GeForce GTX 960M 4 GB", Operating_System="Windows 10 Home",
          Battery="3 hours", Weight="3.2 kg", Keyboard="Backlit")),
    ("lap-04", "Nexora Air NA-13 Ultrabook", "Laptops", "Nexora", 58990, 64990,
     "A slim, lightweight 13.3 inch ultrabook for people who travel and work on the move. The metal body weighs "
     "just 1.3 kg, the Full HD screen is bright and sharp, and the solid state drive wakes the laptop in seconds. "
     "Battery life comfortably covers a working day away from a power point.",
     spec(Processor="Intel Core i5 6th Gen", RAM="8 GB DDR3", Storage="256 GB SSD", Screen="13.3 inch Full HD",
          Graphics="Intel HD Graphics 520", Operating_System="Windows 10 Home", Battery="9 hours", Weight="1.3 kg")),
    ("lap-05", "Orbis Business OB-15 Laptop", "Laptops", "Orbis", 44990, 49990,
     "A dependable 15.6 inch business laptop for office work. It has a spill resistant keyboard, a fingerprint "
     "reader for secure sign in, and a docking connector for a desk setup. The Core i5 processor and 8 GB of "
     "memory handle spreadsheets, presentations and video meetings, and the sturdy build is made for daily travel.",
     spec(Processor="Intel Core i5 6th Gen", RAM="8 GB DDR4", Storage="500 GB HDD", Screen="15.6 inch HD",
          Graphics="Intel HD Graphics 520", Operating_System="Windows 10 Pro", Battery="7 hours", Weight="2.0 kg",
          Security="Fingerprint reader")),
    # ---- Mice ----
    ("mou-01", "Veltrix M100 Wired Optical Mouse", "Mice", "Veltrix", 299, 399,
     "A simple wired optical mouse for everyday computer use. The 1000 DPI sensor tracks smoothly on most desks, "
     "the symmetrical shape suits left and right hands, and the 1.5 metre USB cable plugs in with no software or "
     "batteries needed. A sensible budget companion for a laptop or desktop.",
     spec(Connectivity="Wired USB", Sensor="Optical", DPI="1000", Buttons="3", Cable_Length="1.5 m",
          Compatible_With="Windows, Mac, Linux")),
    ("mou-02", "Orbis W200 Wireless Mouse", "Mice", "Orbis", 649, 799,
     "A compact wireless mouse that connects through a tiny USB receiver which stores inside the mouse for travel. "
     "The 1600 DPI optical sensor works on most surfaces and one AA battery lasts up to a year. It is quiet, "
     "light and a good match for a student laptop.",
     spec(Connectivity="Wireless 2.4 GHz", Sensor="Optical", DPI="1600", Buttons="3", Battery="1 x AA, up to 12 months",
          Range="10 m", Compatible_With="Windows, Mac")),
    ("mou-03", "Nexora Bluetooth BM-300 Mouse", "Mice", "Nexora", 999, 1299,
     "A slim Bluetooth mouse that pairs directly with a laptop or tablet, so no USB port is used. It has a "
     "rechargeable battery, a quiet scroll wheel and an adjustable 800 to 2400 DPI sensor. The low profile body "
     "slips easily into a laptop bag.",
     spec(Connectivity="Bluetooth 4.0", Sensor="Optical", DPI="800 / 1200 / 2400", Buttons="4",
          Battery="Rechargeable, 30 days", Range="10 m", Compatible_With="Windows, Mac, Android")),
    ("mou-04", "Nexora Predator NP-G7 Gaming Mouse", "Mice", "Nexora", 1899, 2499,
     "A wired gaming mouse with a 3200 DPI sensor for fast, accurate aiming. It has six programmable buttons, an "
     "ergonomic grip, adjustable weights and a braided cable that resists tangling. Colour lighting can be changed "
     "or switched off.",
     spec(Connectivity="Wired USB", Sensor="Optical", DPI="Up to 3200", Buttons="6 programmable",
          Cable_Length="1.8 m braided", Lighting="RGB", Compatible_With="Windows")),
    # ---- Keyboards ----
    ("key-01", "Veltrix K110 Wired USB Keyboard", "Keyboards", "Veltrix", 449, 599,
     "A full size wired USB keyboard with a number pad and quiet, soft keys. It works as soon as it is plugged in "
     "and the spill resistant design protects it from small accidents. A dependable keyboard for home, school or "
     "office use.",
     spec(Connectivity="Wired USB", Layout="Full size with numeric keypad", Keys="104", Spill_Resistant="Yes",
          Cable_Length="1.5 m", Compatible_With="Windows, Mac, Linux")),
    ("key-02", "Orbis Duo OD-500 Wireless Keyboard and Mouse Combo", "Keyboards", "Orbis", 1199, 1499,
     "A wireless keyboard and mouse set that share one USB receiver, so only one port is used. The slim keyboard has "
     "quiet keys and a number pad, and the matching optical mouse runs on one battery. The set is ideal for a "
     "tidy desk or a living room media computer.",
     spec(Connectivity="Wireless 2.4 GHz", Layout="Full size with numeric keypad", Range="10 m",
          Battery="2 x AAA keyboard, 1 x AA mouse", Compatible_With="Windows, Mac")),
    ("key-03", "Nexora Mech NK-87 Mechanical Gaming Keyboard", "Keyboards", "Nexora", 3499, 4299,
     "A compact mechanical keyboard with tactile blue switches and a satisfying click. Each key is individually "
     "backlit, the 87 key layout saves desk space and full anti ghosting lets every key press register in fast games. "
     "The detachable cable makes it easy to carry.",
     spec(Connectivity="Wired USB detachable", Layout="Tenkeyless, 87 keys", Switches="Mechanical blue",
          Lighting="RGB per key", Anti_Ghosting="Full N-key", Compatible_With="Windows, Mac")),
    ("key-04", "Veltrix Slim VB-10 Bluetooth Keyboard", "Keyboards", "Veltrix", 1399, 1799,
     "A slim, light Bluetooth keyboard that pairs with a phone, tablet or laptop and switches between up to three "
     "devices at the touch of a key. The rechargeable battery lasts weeks and the compact body fits in a bag.",
     spec(Connectivity="Bluetooth 3.0", Layout="Compact, 78 keys", Devices="Up to 3",
          Battery="Rechargeable, 30 days", Compatible_With="Windows, Mac, Android, iOS")),
    # ---- USB Storage ----
    ("usb-01", "Orbis Swift 16 GB USB 3.0 Pen Drive", "USB Storage", "Orbis", 599, 749,
     "A fast 16 GB USB 3.0 pen drive in a slim metal body with a keyring loop. It copies large files quickly and "
     "also works with older USB 2.0 ports. Good for documents, photos and a few movies.",
     spec(Capacity="16 GB", Interface="USB 3.0", Read_Speed="Up to 100 MB/s", Body="Metal", Warranty="5 years")),
    ("usb-02", "Veltrix Pocket 64 GB USB 3.0 Pen Drive", "USB Storage", "Veltrix", 1299, 1599,
     "A roomy 64 GB USB 3.0 pen drive for large video files, backups and software installers. The retractable "
     "connector has no cap to lose and the drive reads files at up to 120 MB/s. A strong choice for storing "
     "movies and big collections.",
     spec(Capacity="64 GB", Interface="USB 3.0", Read_Speed="Up to 120 MB/s", Body="Plastic, retractable",
          Warranty="5 years")),
    ("usb-03", "Nexora Duo 32 GB OTG Pen Drive", "USB Storage", "Nexora", 799, 999,
     "A 32 GB dual connector pen drive with a USB port at one end and a micro USB port at the other, so files move "
     "between a phone and a computer without a cable. Useful for freeing up phone storage and carrying photos.",
     spec(Capacity="32 GB", Interface="USB 2.0 + micro USB OTG", Read_Speed="Up to 30 MB/s", Body="Metal",
          Warranty="3 years")),
    # ---- Power Banks ----
    ("pwr-01", "Orbis PowerLite 10000 mAh Power Bank", "Power Banks", "Orbis", 899, 1199,
     "A pocket friendly 10000 mAh power bank that charges a typical phone about three times. It has dual USB "
     "outputs so two devices can charge at once, indicator lights for the remaining charge and short circuit and "
     "overcharge protection.",
     spec(Capacity="10000 mAh", Output="2 x USB, 2.1 A total", Input="Micro USB", Indicator="4 LED",
          Protection="Short circuit, overcharge", Weight="220 g")),
    ("pwr-02", "Nexora Max 20000 mAh Power Bank", "Power Banks", "Nexora", 1799, 2299,
     "A high capacity 20000 mAh power bank for long trips. It can charge a phone five or six times or a tablet "
     "twice, has dual fast charging USB ports and a bright LED torch. The aluminium body is sturdy for daily travel.",
     spec(Capacity="20000 mAh", Output="2 x USB, 3.4 A total", Input="Micro USB", Indicator="LED display",
          Protection="Short circuit, overcharge, temperature", Weight="410 g", Extras="LED torch")),
]


def rows() -> list[dict]:
    out = []
    for n, (slug, name, category, brand, price, retail, desc, specs) in enumerate(RECORDS, start=1):
        out.append({
            "product_id": f"S-{slug}", "name": name, "category": category, "brand": brand, "price": float(price),
            "description": desc, "specifications": specs, "source_ref": "SYNTHETIC",
            "source_uniq_id": f"synthetic-{slug}", "source_pid": "", "source_url": "", "source_row": 0,
            "source_category": f"Synthetic >> {category}", "crawl_timestamp": "", "retail_price": float(retail),
            "description_source": "synthetic", "specification_format": "synthetic",
        })
    return out


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows())
    print(f"Wrote {len(RECORDS)} synthetic records to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
