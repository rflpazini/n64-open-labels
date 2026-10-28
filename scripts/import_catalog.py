"""Extract a review backlog from a local Libretro/No-Intro N64 DAT, never ROMs."""
import argparse,csv,hashlib,json,re
from pathlib import Path
SOURCE='https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/Nintendo%20-%20Nintendo%2064.dat'
EXCLUDE=re.compile(r'Proto|Beta|Demo|Aftermarket|Unl|Pirate|LodgeNet|Virtual Console|GameCube|Switch Online|Manual|Audio|Debug|Game Jam|Summer64|Limited Run|Piko Interactive|Itch.io|Zelda Collection|Presence of Mind|E3 1997|Add-on',re.I)
REGIONS={'USA','Europe','Japan','Germany','France','Australia','Italy','Spain','Brazil','USA, Europe','Japan, USA','Europe, Australia','Asia','China','World','Unknown'}
def parse(raw):
 entries={};excluded=set()
 for block in re.findall(r'^game \(\n(.*?)^\)',raw,re.M|re.S):
  name=re.search(r'^\s*name "(.*?)"',block,re.M)[1]
  if EXCLUDE.search(name):excluded.add(name);continue
  tags=re.findall(r'\((.*?)\)',name)
  region=next((t for t in tags if t in REGIONS),'Unknown')
  title=name.split(' (')[0]
  editions=[t for t in tags if t not in REGIONS and not re.fullmatch(r'Rev \d+|v[\d.]+|[A-Z][a-z](?:,[A-Z][a-z])*|PAL|MPAL',t)]
  # Language tags retained: country-specific packaging requires human review.
  language=next((t for t in tags if re.fullmatch(r'[A-Z][a-z](?:,[A-Z][a-z])*',t)),'')
  key=(title,region,language,tuple(editions))
  serial=re.search(r'^\s*serial "(.*?)"',block,re.M)
  if key not in entries:
   entries[key]={'id':hashlib.sha256('|'.join([title,region,language,*editions]).encode()).hexdigest()[:16],'title':title,'region':region,'languages':language,'edition':' / '.join(editions),'status':'needs_catalog_review','source_names':set(),'serials':set(),'source':SOURCE,'recipe':'','art_source':'','logo_source':'','rights_status':'not_reviewed'}
  entries[key]['source_names'].add(name)
  if serial:entries[key]['serials'].add(serial[1])
 result=[]
 for key,item in sorted(entries.items()):
  item['source_names']=' | '.join(sorted(item['source_names']));item['serials']=' | '.join(sorted(item['serials']));result.append(item)
 return result,excluded

def main():
 p=argparse.ArgumentParser();p.add_argument('dat',type=Path);p.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'catalog');a=p.parse_args()
 raw=a.dat.read_bytes();entries,excluded=parse(raw.decode());a.out.mkdir(parents=True,exist_ok=True)
 with (a.out/'coverage.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
 meta={'source':SOURCE,'sha256':hashlib.sha256(raw).hexdigest(),'dat_version':re.search(r'version "(.*?)"',raw.decode())[1],'candidate_regional_entries':len(entries),'excluded_distinct_source_names':len(excluded),'count_is_not_unique_games':True,'method':'Endianness and ROM revision duplicates merged; regional/language editions retained. Not a verified retail checklist. All entries require human review. China/iQue and special editions need scope review.'}
 (a.out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
 (a.out/'excluded.txt').write_text('\n'.join(sorted(excluded))+'\n')
 print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
