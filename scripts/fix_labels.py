"""Apply the hand corrections in catalog/label-fixes.json to the A-Z recipe sets.

auto_recipes.py drafts every label automatically. Some drafts break the shared
layout (no logo, boxed title screen) or land on the wrong part of the box. This
script rebuilds those assets from libretro-thumbnails sources, rewrites the
recipe and status entries, and refreshes the region's asset pack. Run it after
auto_recipes.py, then re-export with export_a_to_z.py.

  python scripts/fix_labels.py --thumbs path/to/Nintendo_-_Nintendo_64
  python scripts/fix_labels.py --download build/thumbs   # fetch only the files it needs

Assets are written to assets/<region>/ (git-ignored) and into
prints/<region>-a-z/<region>-assets.zip. Requires numpy and opencv-python-headless.
"""
import argparse,json,sys,urllib.parse,urllib.request,zipfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from auto_recipes import ASPECT,background,load
UPSTREAM='https://raw.githubusercontent.com/libretro-thumbnails/Nintendo_-_Nintendo_64/master/'
KEYS={'USA':'usa','Japan':'japan'}

def source(a,rel):
 if a.thumbs:return load(a.thumbs/rel)
 path=a.download/rel
 if not path.is_file():
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(urllib.request.urlopen(UPSTREAM+urllib.parse.quote(rel),timeout=60).read())
 # A downloaded symlink is a text file holding the target name, resolved by load().
 return load(path)

def hsv(im):
 x=cv2.cvtColor(im,cv2.COLOR_RGB2HSV);return [x[...,i].astype(int) for i in range(3)]
def keep_big(m,minarea):
 n,lab,st,_=cv2.connectedComponentsWithStats(m.astype(np.uint8),8);out=np.zeros(m.shape,np.uint8)
 for i in range(1,n):
  if st[i,4]>=minarea:out[lab==i]=1
 return out
def fill_holes(m):
 m=m.astype(np.uint8);ff=m.copy();cv2.floodFill(ff,np.zeros((m.shape[0]+2,m.shape[1]+2),np.uint8),(0,0),1);return m|(1-ff)
def soft(m,r):return np.clip(cv2.GaussianBlur(m.astype(np.float32)*255,(0,0),r),0,255)
def rgba(im,alpha):
 out=Image.fromarray(np.dstack([im,alpha]).astype(np.uint8),'RGBA')
 return out.crop(out.getchannel('A').point(lambda v:255 if v>24 else 0).getbbox())
def region(im,box):x0,y0,x1,y1=box;return im[y0:y1,x0:x1]

def logo_file(im,spec):return im.convert('RGBA')

def logo_ink(im,spec):
 """Printed ink on a white box: alpha from darkness, optionally keeping the ink colour."""
 im=region(np.asarray(im.convert('RGB')),spec['region']);hi,lo=spec['threshold']
 a=np.clip((hi-im.min(2).astype(float))/(hi-lo),0,1)*255
 for x0,y0,x1,y1 in spec.get('erase',[]):a[y0:y1,x0:x1]=0  # art bleeding into the logo box
 a*=keep_big(a>40,30)
 ink=im if spec.get('keep_color') else np.zeros_like(im)+np.array([int(spec['color'][i:i+2],16) for i in (1,3,5)])
 return rgba(ink,a)

def logo_red_on_black(im,spec):
 im=region(np.asarray(im.convert('RGB')),spec['region']);h,s,v=hsv(im)
 return rgba(im,soft((v>60)&(s>120),.6))

def logo_grabcut(im,spec):
 im=np.asarray(im.convert('RGB'));x0,y0,x1,y1=spec['rect']
 mask=np.zeros(im.shape[:2],np.uint8);b=np.zeros((1,65));f=np.zeros((1,65))
 cv2.grabCut(cv2.cvtColor(im,cv2.COLOR_RGB2BGR),mask,(x0,y0,x1-x0,y1-y0),b,f,8,cv2.GC_INIT_WITH_RECT)
 m=((mask==1)|(mask==3)).astype(np.uint8);h,s,v=hsv(im)
 if spec.get('drop_grey'):m[(s<70)&(v>70)]=0  # stadium haze between the two title lines
 if spec.get('drop_orange'):m[(h>=8)&(h<=20)&(s>80)]=0  # fire under the lettering
 else:m=fill_holes(m)
 return rgba(im,soft(keep_big(m,150),.7))

def logo_sky(im,spec):
 """Title screen lettering over a flat blue sky: sky is certain background, GrabCut the rest."""
 im=np.asarray(im.convert('RGB'));h,s,v=hsv(im);sky=(h>=95)&(h<=110)&(s>70)&(v>170)  # sky sits at hue 104-105; blue lettering at 113+
 x0,y0,x1,y1=spec['region'];mask=np.full(sky.shape,cv2.GC_PR_FGD,np.uint8);mask[:]=cv2.GC_BGD
 mask[y0:y1,x0:x1]=cv2.GC_PR_FGD;mask[sky]=cv2.GC_BGD
 # Saturated royal blue lettering would otherwise be learned as more sky.
 ink=(h>=112)&(h<=125)&(s>180)&(v>40);ink[:y0]=0;ink[y1:]=0;ink[:,:x0]=0;ink[:,x1:]=0;mask[ink]=cv2.GC_FGD
 b=np.zeros((1,65));f=np.zeros((1,65))
 cv2.grabCut(cv2.cvtColor(im,cv2.COLOR_RGB2BGR),mask,None,b,f,5,cv2.GC_INIT_WITH_MASK)
 return rgba(im,soft(keep_big((mask==1)|(mask==3),120),.5))

def logo_conker(im,spec):
 """The title screen stacks BAD / FUR / DAY. vertically; set them on one line under the script."""
 im=np.asarray(im.convert('RGB'));h,s,v=hsv(im)
 fill=((h>=5)&(h<=24)&(s>120)&(v>110)).astype(np.uint8);zone=np.zeros_like(fill);zone[30:215,100:228]=1;fill*=zone
 script=(((h<=6)|(h>=170))&(s>150)&(v>120)).astype(np.uint8);zone=np.zeros_like(script);zone[8:50,80:180]=1
 script=keep_big(cv2.dilate(script*zone,np.ones((2,2),np.uint8)),6)
 # Assign each letter blob to its line by centre, then grow the bevel back around that line only.
 n,lab,st,cen=cv2.connectedComponentsWithStats(fill,8);cuts=spec['rows'];words=[]
 for k in range(3):
  lo=cuts[k-1] if k else 0;hi=cuts[k] if k<2 else fill.shape[0]
  m=np.isin(lab,[i for i in range(1,n) if st[i,4]>=60 and lo<=cen[i][1]<hi]).astype(np.uint8)
  m=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
  words.append(rgba(im,soft(m,.5)))
 cap=max(w.height for w in words);gap=cap//5
 words=[w.resize((round(w.width*cap/w.height),cap),Image.LANCZOS) for w in words]
 line=Image.new('RGBA',(sum(w.width for w in words)+gap*2,cap))
 x=0
 for w in words:line.alpha_composite(w,(x,0));x+=w.width+gap
 sc=rgba(im,soft(script,.5));sc=sc.resize((round(sc.width*1.8),round(sc.height*1.8)),Image.LANCZOS)
 out=Image.new('RGBA',(line.width,line.height+sc.height-cap//6))
 out.alpha_composite(line,(0,sc.height-cap//6));out.alpha_composite(sc,(cap//4,0))
 return out

METHODS={'file':logo_file,'ink':logo_ink,'red_on_black':logo_red_on_black,'grabcut':logo_grabcut,'sky':logo_sky,'conker':logo_conker}

def window(box,w):
 """Exact 39:16 window around the requested one, kept inside the image."""
 x0,y0,x1,y1=w;cy=(y0+y1)/2;hh=round((x1-x0)/ASPECT)
 top=int(min(max(0,round(cy-hh/2)),box.height-hh));return (x0,top,x1,top+hh)

def main():
 p=argparse.ArgumentParser(description=__doc__.split('\n')[0])
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--thumbs',type=Path,help='Local libretro-thumbnails Nintendo_-_Nintendo_64 checkout')
 g.add_argument('--download',type=Path,help='Cache directory; fetch the needed files from GitHub')
 p.add_argument('--fixes',type=Path,default=ROOT/'catalog/label-fixes.json')
 a=p.parse_args()
 fixes=json.loads(a.fixes.read_text(encoding='utf-8'))['fixes'];touched={}
 for key in sorted({KEYS[f['region']] for f in fixes}):
  recipes_p=ROOT/f'examples/{key}.json';status_p=ROOT/f'examples/{key}-status.json'
  recipes=json.loads(recipes_p.read_text(encoding='utf-8'));status=json.loads(status_p.read_text(encoding='utf-8'))
  by_name={r['name']:r for r in recipes};by_title={s['title']:s for s in status['labels']};touched[key]=[]
  for f in (f for f in fixes if KEYS[f['region']]==key):
   r=by_name[f['title']];s=by_title[f['title']];cid=s['catalog_id']
   logo_rel=f'assets/{key}/logo-{cid}.png';art_rel=f'assets/{key}/art-{cid}.jpg'
   if 'logo' in f:
    logo=METHODS[f['logo']['method']](source(a,f['logo']['source']),f['logo'])
    logo.save(ROOT/logo_rel,optimize=True);r['logo']=logo_rel;touched[key].append(logo_rel)
    s['logo_source']=f"libretro-thumbnails {f['logo']['source']} ({f['logo']['method']})"
   logo=Image.open(ROOT/r['logo']).convert('RGBA')
   box=source(a,f['art']['source']).convert('RGB');x0,y0,x1,y1=window(box,f['art']['window'])
   mx,my=12,8;keep=(max(0,x0-mx),max(0,y0-my),min(box.width,x1+mx),min(box.height,y1+my))
   art=box.crop(keep);art.save(ROOT/art_rel,quality=92);touched[key].append(art_rel)
   crop=[x0-keep[0],y0-keep[1],x1-keep[0],y1-keep[1]]
   for k in ('art_viewport','art_fit','transition','logo_crop'):r.pop(k,None)
   r.update(art=art_rel,crop=crop,background=f.get('background') or background(art,crop,logo))
   s['art_source']=f"libretro-thumbnails {f['art']['source']}";s['hand_fix']=f['reason']
   for k in ('box_title_inliers','crop_check'):s.pop(k,None)
  recipes_p.write_text(json.dumps(recipes,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
  status_p.write_text(json.dumps(status,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
  pack=ROOT/f'prints/{key}-a-z/{key}-assets.zip'
  if pack.is_file():
   with zipfile.ZipFile(pack) as z:old={n:z.read(n) for n in z.namelist() if n not in touched[key]}
   with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
    for n,data in old.items():z.writestr(n,data)
    for n in touched[key]:z.write(ROOT/n,n)
  print(f'{key}: {len(touched[key])} assets rebuilt')

if __name__=='__main__':main()
