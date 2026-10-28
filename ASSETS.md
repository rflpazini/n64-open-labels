# Artwork and third-party material

The MIT license covers only original project materials. It does not grant rights to Nintendo or publisher logos, characters, packaging scans, photographs or other third-party images. A source URL is attribution, not a redistribution license. A noncommercial notice also does not by itself supply permission.

The source distribution includes original demo graphics and the separately licensed DejaVu font. The 18 existing label recipes reference filenames from the owner's earlier personal collection pack; these game image files are deliberately not bundled in this public-source candidate. The generator works with locally supplied images.

Before adding a public artwork pack or printable game-art PDF, record each asset's exact source, creator or rights holder when known, license or permission evidence, and transformations. Mark unresolved items `not_reviewed`; do not present them as freely licensed. Artwork availability on a thumbnail server does not establish redistribution permission.

Suggested asset record:

```json
{
  "path": "assets/game-region-logo.png",
  "source_url": "exact source page or file",
  "rights_holder": "unknown until verified",
  "license_or_permission": "not_reviewed",
  "permission_evidence": "",
  "changes": "transparent crop; no title alteration",
  "edition": "exact game and region"
}
```

Historical research sources for the initial personal collection (per-file mapping is still needed):

- https://github.com/libretro-thumbnails/Nintendo_-_Nintendo_64
- https://gmlabels.blogspot.com/p/n64.html
- https://n64gamemaintenance.weebly.com/game-label-images.html
- https://www.mariowiki.com/Gallery:Donkey_Kong_64
- https://www.nintendo64ever.com/Nintendo-64-Game-Content,636,Perfect-Dark.html
- https://www.zelda-temple.net/media-and-downloads/official-artwork/the-legend-of-zelda-ocarina-of-time

Licensing references:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- https://creativecommons.org/faq/

Rights questions can be raised through a repository issue once the project is published. Do not upload disputed artwork to that issue as evidence when a source link is sufficient.
