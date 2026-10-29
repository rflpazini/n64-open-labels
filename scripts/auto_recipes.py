"""Draft recipes for a whole region from libretro-thumbnails logos and box art.

Reads catalog/coverage.csv, finds each title's Named_Logos and Named_Boxarts
image in a local libretro-thumbnails checkout, picks an art crop that avoids
the box's own printed title, and writes derived assets plus a recipe file.

Every recipe produced here is a machine draft (stage `draft`), not a visually
approved label. Titles already approved in examples/collection-18.json reuse
those recipes. Requires numpy and opencv-python-headless.

  python scripts/auto_recipes.py --thumbs path/to/Nintendo_-_Nintendo_64 \
      --region USA --snap-art catalog/usa-snap-art.txt --out build/usa
"""
import argparse,csv,json,re
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ASPECT=39/16
# Approved collection-18 recipes, keyed by catalog title.
APPROVED={'Mario Kart 64':0,'Kobe Bryant in NBA Courtside':2,'Duke Nukem 64':3,'Super Mario 64':4,'Killer Instinct Gold':5,'Star Fox 64':6,'Perfect Dark':7,'Paper Mario':8,'Donkey Kong 64':10,'Super Smash Bros.':11,'GoldenEye 007':12,'Banjo-Kazooie':13,'Legend of Zelda, The - Ocarina of Time':14,"Legend of Zelda, The - Majora's Mask":15,'Resident Evil 2':16,'Clay Fighter 63 1-3':17}
NOT_GAMES={'GameShark Pro'}

def libretro(name):return re.sub(r'[&*/:`<>?\\|"]','_',name)
def key(s):return re.sub(r'[^a-z0-9]','',s.lower())

def resolve(thumbs,kind,row,region):
 """Exact No-Intro name first, then same title in the region, then Europe."""
 for n in sorted(row['source_names'].split(' | '),key=len):
  p=thumbs/kind/f'{libretro(n)}.png'
  if p.is_file():return p
 cands=sorted(p for p in (thumbs/kind).glob('*.png') if key(p.name.split(' (')[0])==key(row['title']) and 'Unl' not in p.name)
 for tag in (f'({region}',"(Europe"):
  for p in cands:
   if tag in p.name:return p

def load(path):
 # libretro uses git symlinks; a checkout without symlink support stores the target name.
 for _ in range(3):
  if path.read_bytes()[:4]==b'\x89PNG':return Image.open(path)
  path=path.parent/path.read_text().strip()
 raise ValueError(f'Unresolved thumbnail link: {path}')

def art_width(box):
 """US boxes carry a Nintendo 64 spine on the right; keep only the artwork.

 Usually red; otherwise take the strongest vertical edge in the right third.
 Spines start near 81% of the width, so never keep more than 83%.
 """
 a=np.asarray(box,dtype=np.float32);w=a.shape[1];lo,hi=int(w*.68),int(w*.9)
 red=((a[:,:,0]>150)&(a[:,:,1]<90)&(a[:,:,2]<90)).mean(axis=0)
 for x in range(lo,w):
  if red[x:x+6].mean()>.45:return min(x,int(w*.83))
 g=a.mean(axis=2);steady=(np.abs(np.diff(g,axis=1))>8).mean(axis=0)
 return min(lo+int(np.argmax(steady[lo:hi])),int(w*.83))

SIFT=None
def find_logo(gray,logo):
 """Locate the box's printed title by SIFT matching the clean logo; returns (bbox, inliers)."""
 global SIFT
 SIFT=SIFT or cv2.SIFT_create()
 a=np.asarray(logo);alpha=a[:,:,3]
 k1,d1=SIFT.detectAndCompute(cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY),(alpha>100).astype(np.uint8)*255)
 k2,d2=SIFT.detectAndCompute(gray,None)
 if d1 is None or d2 is None or len(k1)<4 or len(k2)<4:return None,0
 good=[m for m,n in (p for p in cv2.BFMatcher().knnMatch(d1,d2,k=2) if len(p)==2) if m.distance<.75*n.distance]
 if len(good)<6:return None,len(good)
 src=np.float32([k1[m.queryIdx].pt for m in good]);dst=np.float32([k2[m.trainIdx].pt for m in good])
 M,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=6)
 if M is None:return None,0
 ys,xs=np.nonzero(alpha>100)
 corners=np.float32([[xs.min(),ys.min()],[xs.max(),ys.min()],[xs.min(),ys.max()],[xs.max(),ys.max()]])@M[:,:2].T+M[:,2]
 H,W=gray.shape;x0,y0=np.clip(corners.min(0),0,(W,H));x1,y1=np.clip(corners.max(0),0,(W,H))
 return (int(x0),int(y0),int(x1),int(y1)),int(inliers.sum())

def choose_crop(box,logo_box):
 """Highest-detail 39:16 window, weighted toward its visible right side, away from the box title."""
 g=np.asarray(box.convert('L'),dtype=np.float32)
 energy=np.abs(cv2.Sobel(g,cv2.CV_32F,1,0))+np.abs(cv2.Sobel(g,cv2.CV_32F,0,1))
 H,W=g.shape;block=np.zeros((H,W),bool)
 # Box titles usually sit in the top band and badges in the bottom band; favour the middle.
 prior=np.ones(H,np.float32);prior[:int(H*.3)]=.35;prior[int(H*.82):]=.3
 energy*=prior[:,None]
 if logo_box:x0,y0,x1,y1=logo_box;block[max(0,y0-8):y1+8,max(0,x0-8):x1+8]=True
 block[int(H*.84):,:int(W*.3)]=True;block[int(H*.84):,int(W*.7):]=True  # publisher and rating marks
 ie=cv2.integral(energy);ib=cv2.integral(block.astype(np.uint8))
 def total(ii,x,y,w,h):return ii[y+h,x+w]-ii[y,x+w]-ii[y+h,x]+ii[y,x]
 best=None
 for frac in (1,.9,.8,.7,.6,.5,.4):
  w=int(W*frac);h=int(w/ASPECT)
  if h>H:continue
  for y in range(0,H-h+1,4):
   for x in range(0,W-w+1,6):
    vx=x+int(w*.35);vw=w-int(w*.35)  # part not covered by the fade and title
    detail=total(ie,vx,y,vw,h)/(vw*h)
    clash=total(ib,vx,y,vw,h)/(vw*h)+.3*total(ib,x,y,w,h)/(w*h)
    # Any visible overlap with the box title ranks below every clean window.
    score=(-clash if clash>.03 else 0,detail*(1-clash)+4*frac)
    if best is None or score>best[0]:best=(score,(x,y,x+w,y+h))
 return best[1]

def luminance(rgb):return (.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2])/255

def background(art,crop,logo):
 """Colour of the crop's left edge, pushed darker or lighter until the title reads."""
 x0,y0,x1,y1=crop;edge=np.asarray(art.crop((x0,y0,x0+max(2,(x1-x0)//8),y1)).convert('RGB')).reshape(-1,3)
 bg=np.median(edge,axis=0)
 a=np.asarray(logo.convert('RGBA')).reshape(-1,4);ink=a[a[:,3]>200][:,:3]
 lum=luminance(ink.mean(axis=0)) if len(ink) else .5
 for _ in range(12):
  if abs(luminance(bg)-lum)>=.35:break
  bg=bg*.75 if lum>.45 else bg+(255-bg)*.3
 return '#%02x%02x%02x'%tuple(int(round(v)) for v in np.clip(bg,0,255))

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0])
 p.add_argument('--thumbs',type=Path,required=True,help='Local libretro-thumbnails Nintendo_-_Nintendo_64 checkout')
 p.add_argument('--region',default='USA');p.add_argument('--out',type=Path,required=True)
 p.add_argument('--snap-art',type=Path,help='Titles whose box art is mostly text; use a Named_Snaps screenshot as art')
 a=p.parse_args()
 rows=[r for r in csv.DictReader((ROOT/'catalog/coverage.csv').open(encoding='utf-8')) if a.region in r['region'].split(', ') and r['title'] not in NOT_GAMES]
 approved=json.loads((ROOT/'examples/collection-18.json').read_text(encoding='utf-8'))
 assets=a.out/'assets'/a.region.lower();assets.mkdir(parents=True,exist_ok=True)
 snap_titles={t.strip() for t in a.snap_art.read_text(encoding='utf-8').splitlines() if t.strip()} if a.snap_art else set()
 recipes=[];status=[];pending=[]
 for r in sorted(rows,key=lambda r:r['title'].lower()):
  base={'catalog_id':r['id'],'title':r['title'],'region':r['region']}
  if r['title'] in APPROVED:
   recipe=dict(approved[APPROVED[r['title']]],name=r['title'])
   recipes.append(recipe);status.append(dict(base,stage='visual_reviewed',source='examples/collection-18.json',rights_status='not_reviewed'));continue
  logo_p=resolve(a.thumbs,'Named_Logos',r,a.region);box_p=resolve(a.thumbs,'Named_Boxarts',r,a.region)
  use_snap=r['title'] in snap_titles
  if use_snap:box_p=resolve(a.thumbs,'Named_Snaps',r,a.region)
  if not (logo_p and box_p):
   pending.append(dict(base,missing=[k for k,v in (('logo',logo_p),('box art',box_p)) if not v]));continue
  logo=load(logo_p).convert('RGBA');box=load(box_p).convert('RGB')
  if use_snap:logo_box,match=None,0
  else:
   box=box.crop((0,0,art_width(box),box.height))
   logo_box,match=find_logo(np.asarray(box.convert('L')),logo)
  crop=choose_crop(box,logo_box if match>=8 else None)
  # Store only the chosen window plus a margin, so recipes stay small.
  mx,my=12,8;x0,y0,x1,y1=crop;keep=(max(0,x0-mx),max(0,y0-my),min(box.width,x1+mx),min(box.height,y1+my))
  art=box.crop(keep);crop=[x0-keep[0],y0-keep[1],x1-keep[0],y1-keep[1]]
  bbox=logo.getchannel('A').getbbox();logo=logo.crop(bbox)
  logo_rel=f'assets/{a.region.lower()}/logo-{r["id"]}.png';art_rel=f'assets/{a.region.lower()}/art-{r["id"]}.jpg'
  logo.save(a.out/logo_rel,optimize=True);art.save(a.out/art_rel,quality=92)
  recipes.append({'name':r['title'],'logo':logo_rel,'art':art_rel,'crop':crop,'background':background(art,crop,logo)})
  status.append(dict(base,stage='draft',logo_source=f'libretro-thumbnails Named_Logos/{logo_p.name}',art_source=f'libretro-thumbnails {box_p.parent.name}/{box_p.name}',box_title_inliers=match,crop_check='box title not located; check the crop for a repeated title' if match<8 and not use_snap else '',rights_status='not_reviewed'))
 (a.out/'recipes.json').write_text(json.dumps(recipes,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
 (a.out/'status.json').write_text(json.dumps({'labels':status,'pending':pending},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
 print(f'{len(recipes)} recipes ({sum(s["stage"]=="draft" for s in status)} drafts), {len(pending)} pending')

if __name__=='__main__':main()
