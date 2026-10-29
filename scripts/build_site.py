"""Assemble the GitHub Pages site from site/ and the published prints.

Copies the static files, every label PNG and PDF, writes small JPEG thumbnails
for the gallery and a labels.json the page reads. Nothing here is committed;
the Pages workflow runs it on every push to main.

  python scripts/build_site.py --out _site
  python -m http.server -d _site 8000
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REPO='rflpazini/n64-open-labels'
# Published A-Z sets: (region shown on the site, folder key under prints/ and examples/).
SETS=[('USA','usa'),('Japan','japan')]

def display(title):
 """No-Intro sort titles to box titles: 'Legend of Zelda, The - X' -> 'The Legend of Zelda: X'."""
 head,sep,tail=title.partition(' - ')
 m=re.fullmatch(r'(.*), (The|A|An)',head)
 if m:head=f'{m[2]} {m[1]}'
 m=re.fullmatch(r'(.*), (The|A|An)',tail)
 if m:tail=f'{m[2]} {m[1]}'
 return head+(': '+tail if sep else '')

def slug(text):return re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')

def thumb(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 with Image.open(src) as im:
  im=im.convert('RGB');im.thumbnail((640,163),Image.Resampling.LANCZOS);im.save(dst,quality=84,optimize=True)

def og(out,labels):
 """1200x630 link preview: a wall of hand-tuned labels."""
 card=Image.new('RGB',(1200,630),'#f8fafc')
 for i,l in enumerate(labels[:16]):
  with Image.open(out/l['thumb']) as im:
   card.paste(im.resize((560,142)),(26+(i%2)*588,18+(i//2)*76))
 card.save(out/'og.jpg',quality=86)

def fingerprint(out):
 """Version asset URLs by content so a cached old app.js never runs against new HTML or data."""
 def tag(path):return hashlib.sha256(path.read_bytes()).hexdigest()[:10]
 app=out/'app.js'
 app.write_text(app.read_text(encoding='utf-8').replace("fetch('labels.json')",f"fetch('labels.json?v={tag(out/'labels.json')}')"),encoding='utf-8')
 page=out/'index.html';html=page.read_text(encoding='utf-8')
 for name in ('app.js','style.css'):html=html.replace(f'"{name}"',f'"{name}?v={tag(out/name)}"')
 page.write_text(html,encoding='utf-8')

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0]);p.add_argument('--out',type=Path,default=ROOT/'_site');a=p.parse_args()
 out=a.out
 if out.exists():shutil.rmtree(out)
 shutil.copytree(ROOT/'site',out)
 labels=[];missing=[]
 for region,key in SETS:
  status=json.loads((ROOT/f'examples/{key}-status.json').read_text(encoding='utf-8'))
  by_title={s['title']:s for s in status['labels']}
  missing+=[f"{display(p['title'])} ({region})" for p in status['pending']]
  for letter,rows in json.loads((ROOT/f'prints/{key}-a-z/index.json').read_text(encoding='utf-8')).items():
   for r in rows:
    s=by_title.get(r['name'],{})
    # USA ids stay bare so earlier shared ?sheet= links keep working; other sets are suffixed (a joint release can be in both).
    cid=s.get('catalog_id') or slug(r['name'])
    labels.append({'id':cid if key=='usa' else f'{cid}-{key}','title':display(r['name']),'sort':r['name'].lower(),'letter':letter,'region':region,
                   'stage':'approved' if r['stage']=='visual_reviewed' else 'draft','png':f'labels/{key}/{r["file"]}','thumb':f'thumbs/{key}/{Path(r["file"]).with_suffix(".jpg")}','sheet':f'labels/{key}/{letter}/labels-A4.pdf'})
  shutil.copytree(ROOT/f'prints/{key}-a-z',out/f'labels/{key}',ignore=shutil.ignore_patterns('*.zip','*.md','preview.jpg','manifest.json','index.json'))
 labels.sort(key=lambda l:(l['sort'],l['region']))
 for l in labels:thumb(out/l['png'],out/l['thumb'])
 og(out,[l for l in labels if l['stage']=='approved'])
 (out/'labels.json').write_text(json.dumps({'repo':REPO,'regions':[r for r,_ in SETS],'labels':labels,'missing':missing},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 fingerprint(out)
 print(f'Site with {len(labels)} labels in {out}')

if __name__=='__main__':main()
