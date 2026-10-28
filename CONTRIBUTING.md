# Contributing a label

1. Pick a candidate in `catalog/coverage.csv`; verify that it is a retail cartridge edition and whether another row represents the same packaging. Preserve local titles. Record aliases rather than guessing translations.
2. Identify the exact regional front label or period box art. Record sources and rights information using ASSETS.md. Do not extract logos from commercial fan sticker sets.
3. Prepare a transparent title logo and suitable artwork. Do not invent typography with AI for the faithful set. Identify whether each source is a front label, box, manual or promotional illustration.
4. Add a recipe. Coordinates in `crop` are source pixels: left, top, right, bottom. `art_viewport`, `transition` and logo placement use millimeters. Image paths resolve relative to the project root. Keep names unique within a recipe file.
5. Run `python build.py --config your-recipes.json --output rendered/your-change`. Review PDF and SVG in actual renderers and inspect the enlarged proof. Check spelling, region, visible title details, crop edges, faces, smooth transition and contrast at physical label size.
6. Print at 100%, measure the ruler and verify cartridge fit. Record printer, paper, measured size and whether the test used adhesive stock. Do not claim physical approval from a screen preview.
7. Submit one title/region with screenshots of the proof, sources, permission evidence where relevant, and a short explanation of crop/transition decisions. Keep printable release assets separate from unresolved submissions.

Suggested stages: `needs_catalog_review`, `needs_art`, `draft`, `visual_reviewed`, `print_tested`. Track rights separately as `not_reviewed`, `permission_recorded` or a specific applicable license. A visual review does not establish redistribution rights.

Do not mark the worldwide set complete by counting DAT records: endian dumps, revisions, languages, reissues and local names can create duplicates.
