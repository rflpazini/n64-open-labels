"""Assemble the GitHub Pages site from site/ and the published prints.

Copies the static files, every label PNG and PDF, writes small JPEG thumbnails
for the gallery and a labels.json the page reads. Nothing here is committed;
the Pages workflow runs it on every push to main.

  python scripts/build_site.py --out _site
  python -m http.server -d _site 8000
"""
import argparse,json,re,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REPO='rflpazini/n64-open-labels'
# collection-18 recipes that are not part of the USA set.
EXTRA={'02-smash-bros-japao.png':('Nintendo All-Star! Dairantou Smash Brothers','Japan'),'10-donkey-kong-64-japao.png':('Donkey Kong 64','Japan')}

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

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0]);p.add_argument('--out',type=Path,default=ROOT/'_site');a=p.parse_args()
 out=a.out
 if out.exists():shutil.rmtree(out)
 shutil.copytree(ROOT/'site',out)
 status={s['title']:s for s in json.loads((ROOT/'examples/usa-status.json').read_text(encoding='utf-8'))['labels']}
 labels=[]
 for letter,rows in json.loads((ROOT/'prints/usa-a-z/index.json').read_text(encoding='utf-8')).items():
  for r in rows:
   s=status.get(r['name'],{})
   labels.append({'id':s.get('catalog_id') or slug(r['name']),'title':display(r['name']),'sort':r['name'].lower(),'letter':letter,'region':'USA',
                  'stage':'approved' if r['stage']=='visual_reviewed' else 'draft','png':f'labels/usa/{r["file"]}','thumb':f'thumbs/usa/{Path(r["file"]).with_suffix(".jpg")}','sheet':f'labels/usa/{letter}/labels-A4.pdf'})
 for file,(title,region) in EXTRA.items():
  labels.append({'id':slug(title+'-'+region),'title':title,'sort':title.lower(),'letter':title[0].upper(),'region':region,'stage':'approved',
                 'png':f'labels/collection-18/{file}','thumb':f'thumbs/collection-18/{Path(file).with_suffix(".jpg")}','sheet':'labels/collection-18/labels-A4.pdf'})
 labels.sort(key=lambda l:(l['sort'],l['region']))
 shutil.copytree(ROOT/'prints/usa-a-z',out/'labels/usa',ignore=shutil.ignore_patterns('*.zip','*.md','preview.jpg','manifest.json','index.json'))
 shutil.copytree(ROOT/'prints/collection-18',out/'labels/collection-18',ignore=shutil.ignore_patterns('*.zip','*.md','preview.jpg','manifest.json'))
 for l in labels:thumb(out/l['png'],out/l['thumb'])
 og(out,[l for l in labels if l['stage']=='approved'])
 pending=[s['title'] for s in json.loads((ROOT/'examples/usa-status.json').read_text(encoding='utf-8'))['pending']]
 (out/'labels.json').write_text(json.dumps({'repo':REPO,'labels':labels,'missing':[display(t) for t in pending]},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print(f'Site with {len(labels)} labels in {out}')

if __name__=='__main__':main()
