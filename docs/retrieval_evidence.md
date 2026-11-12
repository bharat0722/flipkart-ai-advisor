# Phase 2 retrieval evidence

Generated 2026-11-12 07:39 UTC by `python scripts/retrieval_report.py`. Top 5 unique products per query, straight from ChromaDB, with no LLM involved. Scores are cosine similarity (higher is closer). Prices are historical 2015-16 catalogue values; `unknown` means the source had no valid price.

| Index property | Value |
| --- | --- |
| Collection | `flipkart_electronics_v1` in `chroma_db` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dims, cosine) |
| Chunk settings | {'max_record_chars': 800, 'overlap': 75, 'size': 700} |
| Products / chunks | 288 / 863 (254 products split) |
| Input CSV SHA-256 | `f13d7836d8530b4506500738b418e9fe3f54c3711644f04722036aacbd434bc9` |
| Built | 2026-11-12T07:23:52+00:00 |

**Summary: 12 of 14 sample queries passed.**

| ID | Query | Expectation | Result |
| --- | --- | --- | --- |
| Q1 | laptop for students | >= 1 of 5 in Laptops | 2/5 in category - **PASS** |
| Q2 | wifi router for home internet | >= 3 of 5 in Routers & Networking | 5/5 in category - **PASS** |
| Q3 | wireless range extender to boost wifi signal | >= 3 of 5 in Routers & Networking | 5/5 in category - **PASS** |
| Q4 | headphones with mic for calls | >= 3 of 5 in Headphones & Earphones | 5/5 in category - **PASS** |
| Q5 | bluetooth earphones for running | >= 3 of 5 in Headphones & Earphones | 5/5 in category - **PASS** |
| Q6 | portable bluetooth speaker | >= 3 of 5 in Speakers | 2/5 in category - **FAIL** |
| Q7 | fast mobile phone charger | >= 3 of 5 in Chargers & Adapters | 5/5 in category - **PASS** |
| Q8 | laptop power adapter replacement | >= 3 of 5 in Chargers & Adapters | 5/5 in category - **PASS** |
| Q9 | power bank to charge my phone while travelling | >= 2 of 5 in Power Banks | 1/5 in category - **FAIL** |
| Q10 | home theater system for movies | >= 2 of 5 in Home Theater | 5/5 in category - **PASS** |
| Q11 | pen drive to store files | >= 2 of 5 in USB Storage | 3/5 in category - **PASS** |
| Q12 | gaming mouse | >= 1 of 5 in Mice | 2/5 in category - **PASS** |
| Q13 | headphones under 1000 rupees | >= 3 of 5 in Headphones & Earphones; all known prices <= INR 1,000 | 5/5 in category; budget respected - **PASS** |
| Q14 | router under 1500 | >= 3 of 5 in Routers & Networking; all known prices <= INR 1,500 | 5/5 in category; budget respected - **PASS** |

## Q1 - "laptop for students"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.461 | HP 15-ac121tu (Notebook) (Core i3 (5th Gen)/ 4GB/ 1TB/ Win10) (N8M17PA) | Laptops | INR 35,390 | `P-bcb8e456728013a90ba66ab3b1b783ad` | row 9990, chunk 3/3 |
| 2 | 0.450 | HP 15-ac116TX (Notebook) (Core i3 (5th Gen)/ 4GB/ 1TB/ Win10/ 2GB Graph) (N8M19PA) | Laptops | INR 38,890 | `P-85aec4bf3185da7ebcc45003429cbfe2` | row 9989, chunk 3/3 |
| 3 | 0.368 | Rega IT Toshiba Satellite L300-227 L300-229 L300-22N 75 75 Adapter | Chargers & Adapters | INR 699 | `P-8ca3f0d60905eb7c16be64fc9ca1426d` | row 15184, chunk 1/5 |
| 4 | 0.345 | Netgear AC2350 Nighthawk X4 Smart WiFi Router (R7500) | Routers & Networking | INR 14,200 | `P-2f00c8e4b5c02fbec5839b913eeb8eba` | row 6652, chunk 2/2 |
| 5 | 0.330 | Lapguard Acer Aspire 7535Gzm-82_90 90 Adapter | Chargers & Adapters | INR 949 | `P-658e86719c7a50758a741da6dd743ff0` | row 15158, chunk 4/4 |

## Q2 - "wifi router for home internet"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.590 | iBall iB-WRH150N 150 Mbps Wireless N Home Router | Routers & Networking | INR 1,650 | `P-08a2f3209f5170b5ea189b5c6c837ab9` | row 5926, chunk 1/3 |
| 2 | 0.532 | TP-LINK Archer C2 AC750 Wireless Dual Band Gigabit Router | Routers & Networking | INR 3,790 | `P-4cd57b9250ee11b7d828431ab0e36032` | row 7146, chunk 1/4 |
| 3 | 0.531 | GadgetGuru Youth Edition 300 Mbps | Routers & Networking | INR 2,450 | `P-5b65e179daf4f3486b83cc2f6c172ae6` | row 7243, chunk 1/3 |
| 4 | 0.512 | Belkin Basic (N150) Router | Routers & Networking | INR 2,399 | `P-c1f318fab298a1cd7bcd25f72da324ea` | row 6230, chunk 2/3 |
| 5 | 0.509 | iBall Wireless N Router | Routers & Networking | INR 969 | `P-ee417fd5023354d317e7f31f92c6228c` | row 5935, chunk 1/2 |

## Q3 - "wireless range extender to boost wifi signal"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.604 | Netgear WN3000RP Universal Wi-Fi Range Extender | Routers & Networking | INR 2,140 | `P-f25d2701ff23f6749e8e69ca17987993` | row 7481, chunk 1/3 |
| 2 | 0.594 | TP-LINK TL-WA830RE 300 Mbps Wireless N Range Extender | Routers & Networking | INR 1,910 | `P-8f00ee54fc378b4ba18b7acca28329de` | row 7134, chunk 1/3 |
| 3 | 0.588 | Belkin Dual-Band Wireless Range Extender | Routers & Networking | INR 4,399 | `P-9a985171b0680687ffe7f7bcdb735c60` | row 6619, chunk 2/2 |
| 4 | 0.586 | TP-LINK RE200 AC750 Wi-Fi Range Extender | Routers & Networking | INR 3,000 | `P-2cd9bf0cc0763a2d469eb32389f3042d` | row 6420, chunk 1/2 |
| 5 | 0.581 | Netgear WN2500RP Universal Dual Band Wi-Fi Range Extender | Routers & Networking | INR 7,550 | `P-c80b6d380e9eca04177301c3feabafeb` | row 5883, chunk 2/2 |

## Q4 - "headphones with mic for calls"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.515 | Shop Swipe Anti-Radiation Retro Style Wired Headphones | Headphones & Earphones | INR 559 | `P-eadd1a659f6acfc0a27321f1b0fe3d30` | row 7922, chunk 2/5 |
| 2 | 0.467 | LIFE LIKE HBS-730 WITH MIC Wireless Bluetooth Headset | Headphones & Earphones | INR 575 | `P-daf4493e6e8ef03c4c076abef86c553e` | row 8018, chunk 2/3 |
| 3 | 0.462 | Steelseries Siberia 200 Wired Headset | Headphones & Earphones | INR 5,999 | `P-5b712f613215c5f674207c4ba51b840b` | row 1317, chunk 2/3 |
| 4 | 0.449 | LIFE LIKE STN-840 4.1 WITH MIC Wireless Bluetooth Headset | Headphones & Earphones | INR 899 | `P-85746bd7ec397edbd4f727ab0f381cca` | row 7956, chunk 2/3 |
| 5 | 0.433 | GND Wired Earphones Dynamic Handsfree Wired Headset | Headphones & Earphones | INR 179 | `P-81df14e9c6419658dc459c232bcbb368` | row 18660, chunk 7/7 |

## Q5 - "bluetooth earphones for running"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.528 | Dhhan Earphones/Handfree for Iphone 4/4s/4g/5/5c/5s Stereo Dynamic Headphone Wired Bluetooth Headphones | Headphones & Earphones | INR 399 | `P-685aef6aaa5cf32d29cab2b7a2e054ac` | row 19088, chunk 1/4 |
| 2 | 0.515 | LIFE LIKE OTP-200 WITH MIC Wireless Bluetooth Headset | Headphones & Earphones | INR 599 | `P-3832bb8399d1e816894bbca03499739b` | row 8008, chunk 2/3 |
| 3 | 0.507 | LIFE LIKE S450 3.0 WITH MIC GOOD SOUND QUALITY Wired & Wireless Bluetooth Headphones | Headphones & Earphones | INR 999 | `P-136454e94f8b20fd332f510601919c2c` | row 7931, chunk 3/4 |
| 4 | 0.494 | CHKOKKO Earbud Skin Wireless Bluetooth Headset | Headphones & Earphones | INR 610 | `P-33e0859ec596d53fb296199218f8cfe7` | row 9186, chunk 1/4 |
| 5 | 0.485 | LIFE LIKE HBS-730 WITH MIC Wireless Bluetooth Headset | Headphones & Earphones | INR 575 | `P-daf4493e6e8ef03c4c076abef86c553e` | row 8018, chunk 2/3 |

## Q6 - "portable bluetooth speaker"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.519 | Janhvi Bluetooth Beatz Pill F Wireless Home Audio Speaker | Speakers | INR 595 | `P-d3257d2c1507aa22cbb274a8402aa16b` | row 7589, chunk 6/6 |
| 2 | 0.485 | Sony HT-GT1 2.1 Home Theatre System | Home Theater | INR 18,990 | `P-7c0ff0a4b4e32a55edc8544a065c5cec` | row 18439, chunk 5/10 |
| 3 | 0.462 | LG DH313OS 5.1 Home Theatre System | Home Theater | INR 7,900 | `P-fdb9d53b85041d6b9590fd6e054a86e0` | row 16236, chunk 2/3 |
| 4 | 0.457 | Shortkut enterprises Model no 428 Mobile/Tablet Speaker | Speakers | INR 449 | `P-b341fafb3d2f2309b3fb4011a15d5a7e` | row 1168, chunk 2/2 |
| 5 | 0.445 | Tech Yug BH-503 bluethooth headset Wireless Bluetooth Headset | Headphones & Earphones | INR 850 | `P-94d3bd221c11b49f7a92cbc445414d0c` | row 5508, chunk 2/2 |

## Q7 - "fast mobile phone charger"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.608 | D'clair Micromax Bolt A075 Battery Charger | Chargers & Adapters | INR 400 | `P-49922eca58b4982784eb1915d29ad1b6` | row 1060, chunk 1/2 |
| 2 | 0.604 | D'clair Micromax Bolt Q324 Battery Charger | Chargers & Adapters | INR 400 | `P-c7a90fcb8149daa1cba761fb28d0aea5` | row 1025, chunk 1/2 |
| 3 | 0.594 | D'clair Huwai Honor 4X Battery Charger | Chargers & Adapters | INR 400 | `P-1adc62302d19c52dc67da80dc5afe2c0` | row 1018, chunk 1/2 |
| 4 | 0.575 | D'clair Micromax A46 Battery Charger | Chargers & Adapters | INR 400 | `P-771687605b6817bda7fd00293d838211` | row 1013, chunk 1/2 |
| 5 | 0.572 | D'clair Lava Al Fa Battery Charger | Chargers & Adapters | INR 400 | `P-b9cfae933a7efb3506bc9df4de6acd49` | row 1058, chunk 1/2 |

## Q8 - "laptop power adapter replacement"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.686 | Rega IT Toshiba Satellite L300-227 L300-229 L300-22N 75 75 Adapter | Chargers & Adapters | INR 699 | `P-8ca3f0d60905eb7c16be64fc9ca1426d` | row 15184, chunk 1/5 |
| 2 | 0.683 | Rega IT Hp Pavilion DV9751XX DV9752EO 65 Adapter | Chargers & Adapters | INR 699 | `P-b8418cc8c1e7877c13738c53549a5f06` | row 15178, chunk 1/5 |
| 3 | 0.680 | Rega IT Asus U33JC-RX044V U33JC-RX067V 90 90 Adapter | Chargers & Adapters | INR 699 | `P-ddb032cfc07724d88710d3ad70fcc08f` | row 15155, chunk 1/5 |
| 4 | 0.674 | Rega IT Hp Pavilion DV1629TN DV1629US 90 Adapter | Chargers & Adapters | INR 699 | `P-91c4586047596cbea0efc116bd9b12f6` | row 15177, chunk 1/5 |
| 5 | 0.668 | Rega IT Hp Pavilion G4-1302AX G4-1302TU (65) 65 Adapter | Chargers & Adapters | INR 699 | `P-af57054325ddaf15d86f4f60e4312a13` | row 15210, chunk 1/5 |

## Q9 - "power bank to charge my phone while travelling"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.593 | Wayona 10000mAh Wireless 10000mAh Power bank With Dual USB Output 10000 mAh | Power Banks | INR 2,149 | `P-b381180b1795b4a37b3782dc4b60d6d9` | row 10485, chunk 2/5 |
| 2 | 0.481 | D'clair Micromax Canvas Play 4G Q469 Battery Charger | Chargers & Adapters | INR 400 | `P-ae5f7ee4c38b73b64d7be051f5251a10` | row 992, chunk 1/2 |
| 3 | 0.474 | D'clair Lava Al Fa Battery Charger | Chargers & Adapters | INR 400 | `P-b9cfae933a7efb3506bc9df4de6acd49` | row 1058, chunk 1/2 |
| 4 | 0.472 | D'clair Micromax Bolt A075 Battery Charger | Chargers & Adapters | INR 400 | `P-49922eca58b4982784eb1915d29ad1b6` | row 1060, chunk 1/2 |
| 5 | 0.469 | D'clair Micromax Bolt Q324 Battery Charger | Chargers & Adapters | INR 400 | `P-c7a90fcb8149daa1cba761fb28d0aea5` | row 1025, chunk 1/2 |

## Q10 - "home theater system for movies"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.550 | DH-Discovery 20200W 2.1 Home Theatre System | Home Theater | INR 6,499 | `P-bf2d00839cec492ea6b86d171f17d98c` | row 18405, chunk 2/4 |
| 2 | 0.547 | LG DH313OS 5.1 Home Theatre System | Home Theater | INR 7,900 | `P-fdb9d53b85041d6b9590fd6e054a86e0` | row 16236, chunk 3/3 |
| 3 | 0.533 | Mr Plus 2827 2.1 Home Theatre System | Home Theater | INR 3,990 | `P-30637f342bc01bd684aace19eb5171a0` | row 16197, chunk 1/3 |
| 4 | 0.499 | Sony HT-GT1 2.1 Home Theatre System | Home Theater | INR 18,990 | `P-7c0ff0a4b4e32a55edc8544a065c5cec` | row 18439, chunk 10/10 |
| 5 | 0.493 | Tecnia TA 422FM 4.1 Home Theatre System | Home Theater | INR 2,690 | `P-ef128da98969ae5db94031f71970ef7a` | row 16347, chunk 1/4 |

## Q11 - "pen drive to store files"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.601 | Via Flowers Llp Mirror VC89564 8 GB Pen Drive | USB Storage | INR 499 | `P-136f448a3e2868a5b9124e1196168bff` | row 18905, chunk 1/3 |
| 2 | 0.504 | Shopizone BMW Wheel 32 GB Pen Drive | USB Storage | INR 999 | `P-a63eecfbb02004863fa1f29a0b8105fc` | row 3268, chunk 1/2 |
| 3 | 0.421 | HP v220w 16 GB Pen Drive | USB Storage | INR 550 | `P-650e27dff8f645649353743f64e03f77` | row 7949, chunk 1/1 |
| 4 | 0.322 | Belkin Play Max Router | Routers & Networking | INR 8,199 | `P-303b2cc1a682291b94061b7633f23c9d` | row 6975, chunk 3/3 |
| 5 | 0.287 | TP-LINK Archer C2 AC750 Wireless Dual Band Gigabit Router | Routers & Networking | INR 3,790 | `P-4cd57b9250ee11b7d828431ab0e36032` | row 7146, chunk 2/4 |

## Q12 - "gaming mouse"

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.511 | Ocean Q3 Wireless Optical Mouse Gaming Mouse | Mice | INR 339 | `P-1ae68e922242e296b3f374362cea696c` | row 5493, chunk 1/1 |
| 2 | 0.496 | Technotech Q3 Wireless Optical Mouse Gaming Mouse | Mice | INR 339 | `P-1a304ee48c38d3bf40eecfb50b410404` | row 5482, chunk 1/1 |
| 3 | 0.319 | RoQ Slim Multimedia 105key Flexible Wired USB Flexible Keyboard | Keyboards | INR 399 | `P-b4d35b6536b623c83b293eb3a1c02bba` | row 982, chunk 3/3 |
| 4 | 0.284 | GadgetGuru Youth Edition 300 Mbps | Routers & Networking | INR 2,450 | `P-5b65e179daf4f3486b83cc2f6c172ae6` | row 7243, chunk 3/3 |
| 5 | 0.278 | HP v220w 16 GB Pen Drive | USB Storage | INR 550 | `P-650e27dff8f645649353743f64e03f77` | row 7949, chunk 1/1 |

## Q13 - "headphones under 1000 rupees" (max_price=1000)

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.537 | boom premium quality s-450-p Dynamic Wired Headphones | Headphones & Earphones | INR 299 | `P-b9e2f194f276ff7c73489e1b3d0c1784` | row 18937, chunk 3/3 |
| 2 | 0.525 | NEWGEN TECH EO-HS3303 236 Wired Headset | Headphones & Earphones | INR 199 | `P-39edf5247c68675e1c63213c0ddb4395` | row 17954, chunk 4/4 |
| 3 | 0.514 | Shop Swipe Anti-Radiation Retro Style Wired Headphones | Headphones & Earphones | INR 559 | `P-eadd1a659f6acfc0a27321f1b0fe3d30` | row 7922, chunk 5/5 |
| 4 | 0.513 | RJ philips Earphone 23000 Stereo Dynamic Headphone Wired Headphones | Headphones & Earphones | INR 399 | `P-b06840ec066994aa351c79bc34fa8d26` | row 7895, chunk 3/3 |
| 5 | 0.496 | DEBOCK DEBOCK Earphone For Samsung galaxy s advance i9070 Stereo Dynamic Headphone Wired Headphones | Headphones & Earphones | INR 320 | `P-c9e5e9b915f201516c40ed6c0b02e405` | row 1285, chunk 4/4 |

## Q14 - "router under 1500" (max_price=1500)

| # | Score | Product | Category | Price | Product ID | Source |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.594 | iBall 150M eXtreme Wireless-N Router | Routers & Networking | INR 929 | `P-261a8e53f715b46fb852f64c150deb49` | row 6264, chunk 2/3 |
| 2 | 0.577 | Digisol 150 Mbps Wireless Green Broadband Router | Routers & Networking | INR 1,299 | `P-8116bd28bf74c5930426fd53a9b4d1cb` | row 7288, chunk 2/3 |
| 3 | 0.571 | TP-LINK TL-WR841N 300Mbps Wireless N Router | Routers & Networking | INR 1,118 | `P-acaedb6dd1ff23f1193ed1233f6358d0` | row 6442, chunk 3/4 |
| 4 | 0.565 | D-Link DIR-600 N150 Wireless Router | Routers & Networking | INR 999 | `P-a6457a53fb964becff312f738a7ba17b` | row 7153, chunk 2/3 |
| 5 | 0.545 | Toto Link ND150 Wireless N ADSL2 Modem 150 Mbps Router | Routers & Networking | INR 1,270 | `P-f93dd8699ffdddbe102baccbfab0936e` | row 7114, chunk 2/3 |
