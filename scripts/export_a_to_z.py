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

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0])
 p.add_argument('--config',type=Path,required=True);p.add_argument('--status',type=Path,required=True)
 p.add_argument('--asset-pack',type=Path);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--dpi',type=int,default=export_collection.DPI)
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
 print(f'Exported {sum(len(r) for _,r in index)} labels in {len(index)} folders to {a.output}')

if __name__=='__main__':main()
