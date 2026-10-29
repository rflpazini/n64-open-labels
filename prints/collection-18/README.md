# Initial collection: 18 printable N64 end labels

[**Download the A4 PDF**](labels-A4.pdf) · [**Source images ZIP**](collection-18-assets.zip) · [**Export manifest**](manifest.json)

Print on A4 at **100% / actual size**, without “fit to page”. Each label is **63 × 16 mm**. Check that the calibration ruler measures **50 mm**. Start with plain paper; physical fit and print-color validation are still pending.

![Collection preview](preview.jpg)

## Individual images

PNGs are 1488 × 378 pixels with 600 DPI metadata. For accurate printing, prefer the PDF. Scan quality varies by source; 600 DPI export does not restore missing detail.

| Game / edition | PNG |
| --- | --- |
| Mario Kart 64 | [Download](01-mario-kart-64.png) |
| Smash Bros. / Japão | [Download](02-smash-bros-japao.png) |
| Kobe Bryant in NBA Courtside | [Download](03-kobe-bryant-in-nba-courtside.png) |
| Duke Nukem 64 | [Download](04-duke-nukem-64.png) |
| Super Mario 64 | [Download](05-super-mario-64.png) |
| Killer Instinct Gold | [Download](06-killer-instinct-gold.png) |
| Star Fox 64 | [Download](07-star-fox-64.png) |
| Perfect Dark | [Download](08-perfect-dark.png) |
| Paper Mario | [Download](09-paper-mario.png) |
| Donkey Kong 64 / Japão | [Download](10-donkey-kong-64-japao.png) |
| Donkey Kong 64 / EUA | [Download](11-donkey-kong-64-eua.png) |
| Super Smash Bros. / EUA | [Download](12-super-smash-bros-eua.png) |
| GoldenEye 007 | [Download](13-goldeneye-007.png) |
| Banjo-Kazooie | [Download](14-banjo-kazooie.png) |
| Zelda: Ocarina of Time | [Download](15-zelda-ocarina-of-time.png) |
| Zelda: Majora’s Mask | [Download](16-zelda-majoras-mask.png) |
| Resident Evil 2 | [Download](17-resident-evil-2.png) |
| ClayFighter 63⅓ | [Download](18-clayfighter-6313.png) |

## Regenerate

From the repository root, install `requirements.txt` and Poppler, then run:

```sh
python export_collection.py --config examples/collection-18.json --asset-pack prints/collection-18/collection-18-assets.zip --output rendered/collection
```

This is the initial collection, not the complete worldwide N64 catalog. The 867 candidate catalog entries are a review backlog and do not represent finished images.

Game logos, characters and source artwork remain third-party material outside the MIT license. See [ASSETS.md](../../ASSETS.md). Exact per-file source mapping and rights review are pending.
