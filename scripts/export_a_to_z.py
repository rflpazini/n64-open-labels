"""Export a recipe set as one printable folder per initial letter (0-9, A ... Z).

Each folder gets its own A4 PDF, PNGs, preview and manifest via export_collection.
A README index lists every label with its stage from the status file.

  python scripts/export_a_to_z.py --config examples/usa.json \
      --status examples/usa-status.json --asset-pack prints/usa-a-z/usa-assets.zip \
      --output prints/usa-a-z --dpi 300
"""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import export_collection

def letter(name):
 c=name[:1].upper()
 return c if c.isalpha() else '0-9'

def write_readme(a,index,status):
 labels=status['labels'];n=sum(len(r) for _,r in index)
 reviewed=sum(s['stage']=='visual_reviewed' for s in labels)
 snaps=sum('Named_Snaps' in s.get('art_source','') for s in labels)
 titled=sum('printed title' in s.get('art_source','') for s in labels)
 L=[f'# {a.region} set, A to Z: printable N64 end labels\n',
  f'**{n} labels** for the {a.region} retail cartridges in `catalog/coverage.csv`, one folder per initial letter. Each folder has an A4 PDF (print at **100% / actual size**), {a.dpi} DPI PNGs, a preview and a manifest. The easiest way to print is the site: https://rflpazini.com/n64-open-labels/\n',
  '## Status\n',
  f'- **{reviewed}** reuse the hand-tuned recipes from [collection-18](../collection-18/).',
  f'- **{n-reviewed}** are machine drafts (`stage: draft`) from `scripts/auto_recipes.py`: libretro-thumbnails logo over an automatic box-art crop. {snaps} use a gameplay screenshot because the box is mostly text; {titled} have no clean logo upstream and use a hand-picked crop that already shows the printed title (`catalog/title-art.json`).',
  '- Drafts are not individually reviewed or print-tested. Report problems with an issue.',
  '- Logos and artwork belong to Nintendo and the publishers (`rights_status: not_reviewed`). Unofficial, non-commercial fan project.\n']
 if status['pending']:L.append('**Not yet included:** '+', '.join(p['title'] for p in status['pending'])+'\n')
 L+=['## Jump to\n',' · '.join(f'[{k}](#{k.lower()})' for k,_ in index)+'\n']
 stage={s['title']:s['stage'].replace('_',' ') for s in labels}
 for k,rows in index:
  L+=[f'## {k}\n',f'[A4 PDF]({k}/labels-A4.pdf) · [Preview]({k}/preview.jpg) · {len(rows)} labels\n','| Game | PNG | Stage |','| --- | --- | --- |']
  L+=[f"| {name} | [PNG]({k}/{file.replace(' ','%20')}) | {stage.get(name,'')} |" for name,file,_ in rows]+['']
 (a.output/'README.md').write_text('\n'.join(L)+'\n',encoding='utf-8')

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0])
 p.add_argument('--config',type=Path,required=True);p.add_argument('--status',type=Path,required=True)
 p.add_argument('--asset-pack',type=Path);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--dpi',type=int,default=export_collection.DPI)
 p.add_argument('--region',default='USA',help='Region name used in the folder README')
 a=p.parse_args()
 recipes=json.loads(a.config.read_text(encoding='utf-8'))
 status=json.loads(a.status.read_text(encoding='utf-8'))
 stage={s['title']:s['stage'] for s in status['labels']}
 groups={}
 for r in recipes:groups.setdefault(letter(r['name']),[]).append(r)
 index=[]
 with tempfile.TemporaryDirectory() as scratch:
  for key in sorted(groups,key=lambda k:(k!='0-9',k)):
   config=Path(scratch)/f'{key}.json';config.write_text(json.dumps(groups[key],ensure_ascii=False),encoding='utf-8')
   export_collection.export(config,a.output/key,a.asset_pack,a.dpi)
   manifest=json.loads((a.output/key/'manifest.json').read_text(encoding='utf-8'))
   index.append((key,[(m['name'],m['file'],stage.get(m['name'],'')) for m in manifest]))
 (a.output/'index.json').write_text(json.dumps({k:[{'name':n,'file':f'{k}/{f}','stage':s} for n,f,s in rows] for k,rows in index},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
 write_readme(a,index,status)
 print(f'Exported {sum(len(r) for _,r in index)} labels in {len(index)} folders to {a.output}')

if __name__=='__main__':main()
