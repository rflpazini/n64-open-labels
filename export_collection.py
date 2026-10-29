"""Export completed recipes as printable PDF, individual PNGs and a gallery.

Uses the same renderer as build.py. Requires Poppler's pdftoppm on PATH.
An optional ZIP supplies recipe assets without installing them in the checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageFile
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

import build

ROOT = Path(__file__).resolve().parent
DPI = 600


def slug(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def export(config, output, asset_pack=None, dpi=DPI):
    pixels = (round(63 / 25.4 * dpi), round(16 / 25.4 * dpi))
    poppler = shutil.which('pdftoppm')
    if not poppler:
        raise ValueError('Install Poppler first: apt install poppler-utils, or brew install poppler.')
    records = json.loads(config.read_text(encoding='utf-8'))
    original_root, original_out, original_items = build.ROOT, build.OUT, build.items
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        try:
            if asset_pack:
                # Copy only referenced files. Never extract arbitrary ZIP paths.
                with zipfile.ZipFile(asset_pack) as archive:
                    for name in sorted({row[key] for row in records for key in ('art', 'logo') if row[key]}):
                        path = Path(name)
                        if path.is_absolute() or '..' in path.parts or path.parts[0] != 'assets':
                            raise ValueError(f'Unsafe asset path: {name}')
                        target = scratch / path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.read(name))
                build.ROOT = scratch
            build.items = build.load_items(config)
            allow_truncated = ImageFile.LOAD_TRUNCATED_IMAGES
            try:
                ImageFile.LOAD_TRUNCATED_IMAGES = False
                for name in sorted({row[key] for row in build.items for key in ('art', 'logo') if row[key]}):
                    try:
                        with Image.open(build.ROOT / name) as source:
                            source.load()
                    except OSError as exc:
                        raise ValueError(f'Invalid or truncated image: {name}') from exc
            finally:
                ImageFile.LOAD_TRUNCATED_IMAGES = allow_truncated
            output.mkdir(parents=True, exist_ok=True)
            build.OUT = scratch / 'pages'
            build.OUT.mkdir()
            build.main()
            shutil.copy2(build.OUT / 'n64-end-labels-padronizadas-A4.pdf', output / 'labels-A4.pdf')
            manifest = []
            font = ImageFont.truetype(str(ROOT / 'assets/DejaVuSans.ttf'), 18)
            preview = Image.new('RGB', (1340, 80 + ((len(build.items) + 1) // 2) * 212), '#f4f2ec')
            draw = ImageDraw.Draw(preview)
            draw.text((30, 24), 'N64 OPEN LABELS | Collection preview | Print the A4 PDF at 100%', font=font, fill='#243038')
            for index, item in enumerate(build.items):
                stem = f'{index + 1:02d}-{slug(item["name"])}'
                single_pdf = scratch / f'{stem}.pdf'
                c = canvas.Canvas(str(single_pdf), pagesize=(63 * mm, 16 * mm))
                build.label(c, item, 0, 0)
                c.showPage()
                c.save()
                target = scratch / stem
                subprocess.run([poppler, '-singlefile', '-png', '-r', str(dpi),
                                '-scale-to-x', str(pixels[0]), '-scale-to-y', str(pixels[1]),
                                str(single_pdf), str(target)], check=True, capture_output=True)
                png = output / f'{stem}.png'
                with Image.open(target.with_suffix('.png')) as source:
                    im = source.convert('RGB')
                im.save(png, dpi=(dpi, dpi))
                x, y = 30 + (index % 2) * 660, 80 + (index // 2) * 212
                draw.text((x, y), item['name'], font=font, fill='#243038')
                preview.paste(im.resize((630, 160), Image.Resampling.LANCZOS), (x, y + 28))
                manifest.append({'recipe_index': index, 'name': item['name'], 'file': png.name,
                                 'width_mm': 63, 'height_mm': 16, 'dpi': dpi,
                                 'pixels': list(pixels), 'sha256': hashlib.sha256(png.read_bytes()).hexdigest()})
            preview.save(output / 'preview.jpg', quality=94)
            (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'Exported {len(manifest)} PNGs, A4 PDF, preview and manifest to {output}')
        finally:
            build.ROOT, build.OUT, build.items = original_root, original_out, original_items


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'examples/demo.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'rendered/export')
    parser.add_argument('--asset-pack', type=Path)
    parser.add_argument('--dpi', type=int, default=DPI, help='PNG resolution (default 600)')
    args = parser.parse_args()
    try:
        export(args.config, args.output, args.asset_pack, args.dpi)
    except (ValueError, KeyError, FileNotFoundError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Error: {exc}\n')
