"""N64 Label System 2.0. All titles use ONE renderer and ONE geometry."""
from pathlib import Path
import json,base64,html,math,hashlib,argparse
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfdoc
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'rendered';OUT.mkdir(exist_ok=True)
FONT=str(ROOT/'assets/DejaVuSans.ttf')
if Path(FONT).exists():
 pdfmetrics.registerFont(TTFont('Body',FONT));FONTNAME='Body'
else:FONTNAME='Helvetica'
LABEL_W=63;LABEL_H=16
LOGO=(1.8,1.3,32.5,13.4)
ART=(24,0,39,16)
items=[]
def load_items(path):
 data=json.loads(path.read_text(encoding='utf-8'))
 if not data:raise ValueError('No labels selected')
 names=[item.get('name') for item in data]
 if len(names)!=len(set(names)):raise ValueError('Recipe names must be unique, including the region')
 for item in data:
  for key in ('name','logo','art','crop','background'):
   if key not in item:raise ValueError(f"Missing {key}: {item}")
  for key in ('logo','art'):
   # A null logo means the title is already part of the artwork.
   if item[key] is None and key=='logo':continue
   if not (ROOT/item[key]).is_file():raise ValueError(f"Missing asset: {item[key]}. See ASSETS.md.")
  if len(item['crop'])!=4:raise ValueError('crop needs four coordinates')
 return data

def stable_id(value):
 return hashlib.sha256(str(value).encode()).hexdigest()[:16]

def label(c,item,x,y,w=63*mm,h=16*mm):
 c.saveState();c.translate(x,y);c.scale(w/63,h/16)
 clip=c.beginPath();clip.rect(0,0,63,16);c.clipPath(clip,stroke=0,fill=0)
 sv=[]
 def rect(x,y,w,h,col):
  c.setFillColor(HexColor(col));c.rect(x,16-y-h,w,h,fill=1,stroke=0)
  sv.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}"/>')
 def image(file,bbox,x,y,w,h,cover=True):
  im=Image.open(file);iw,ih=im.size;a,b,d,e=bbox;bw=d-a;bh=e-b
  assert bw>0 and bh>0 and 0<=a<d<=iw and 0<=b<e<=ih,(file,bbox,im.size)
  s=(max if cover else min)(w/bw,h/bh);xx=x+(w-bw*s)/2-a*s;yy=y+(h-bh*s)/2-b*s
  left=max(x,xx+a*s);top=max(y,yy+b*s);right=min(x+w,xx+d*s);bottom=min(y+h,yy+e*s)
  c.saveState();p=c.beginPath();p.rect(left,16-bottom,right-left,bottom-top);c.clipPath(p,stroke=0,fill=0)
  c.drawImage(str(file),xx,16-yy-ih*s,iw*s,ih*s,mask='auto');c.restoreState()
  mime='image/png' if im.format=='PNG' else 'image/jpeg'
  im.close()
  data=base64.b64encode(file.read_bytes()).decode()
  uid='clip'+stable_id((item['name'],len(sv)))
  sv.append(f'<defs><clipPath id="{uid}" clipPathUnits="userSpaceOnUse"><rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/></clipPath></defs><g clip-path="url(#{uid})"><image x="{xx}" y="{yy}" width="{iw*s}" height="{ih*s}" xlink:href="data:{mime};base64,{data}"/></g>')
 def poly(points,col):
  c.setFillColor(HexColor(col));p=c.beginPath();p.moveTo(points[0][0],16-points[0][1])
  for a,b in points[1:]:p.lineTo(a,16-b)
  p.close();c.drawPath(p,fill=1,stroke=0)
  sv.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in points)+'" fill="'+col+'"/>')
 def dissolve(col,a,b):
  # A true PDF luminosity soft mask: no raster bands or overlapping strips.
  fun=pdfdoc.PDFExponentialFunction([1],[0],1)
  shade=pdfdoc.PDFAxialShading(a,0,b,0,fun,'DeviceGray',Extend=pdfdoc.PDFArray([pdfdoc.PDFtrue,pdfdoc.PDFtrue]))
  resources=pdfdoc.PDFDictionary({'Shading':pdfdoc.PDFDictionary({'S':c._doc.Reference(shade)})})
  form=pdfdoc.PDFStream(pdfdoc.PDFDictionary({'Type':pdfdoc.PDFName('XObject'),'Subtype':pdfdoc.PDFName('Form'),'BBox':pdfdoc.PDFArray([0,0,63,16]),'Resources':resources,'Group':pdfdoc.PDFDictionary({'S':pdfdoc.PDFName('Transparency'),'CS':pdfdoc.PDFName('DeviceGray'),'I':pdfdoc.PDFtrue})}),content=b'/S sh')
  mask=pdfdoc.PDFDictionary({'S':pdfdoc.PDFName('Luminosity'),'G':c._doc.Reference(form)})
  c.saveState();c._extgstate.defaults['SMask']=None;c._extgstate.set(c,'SMask',mask)
  c.setFillColor(HexColor(col));c.rect(0,0,63,16,fill=1,stroke=0);c.restoreState()
  uid='m'+stable_id(item['name'])
  sv.append(f'<defs><linearGradient id="{uid}g" gradientUnits="userSpaceOnUse" x1="{a}" y1="0" x2="{b}" y2="0"><stop offset="0" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="63" height="16"><rect width="63" height="16" fill="url(#{uid}g)"/></mask></defs><rect width="63" height="16" fill="{col}" mask="url(#{uid})"/>')
 rect(0,0,63,16,item['background'])
 if item.get('background_style')=='court':
  # The NBA reference uses court geometry as the environment, without a portrait.
  for j in range(32):rect(j*2,0,.06,16,'#c6a474')
  poly([(28,16),(59,0),(63,0),(63,16)],'#f1e8d4')
  poly([(35,16),(63,1),(63,16)],'#b82b22')
 else:
  # art_fit 'contain' shows the whole crop centred on the background instead of filling the viewport.
  image(ROOT/item['art'],item['crop'],*item.get('art_viewport',ART),item.get('art_fit')!='contain')
  if item.get('transition',[24,43]):dissolve(item['background'],*item.get('transition',[24,43]))
 if item['logo']:
  f=ROOT/item['logo'];im=Image.open(f)
  bb=item.get('logo_crop') or (im.getchannel('A').getbbox() if 'A' in im.getbands() else (0,0,*im.size))
  im.close()
  image(f,bb,*LOGO,False)
 c.restoreState();uid='labelclip'+stable_id(item['name'])
 return f'<defs><clipPath id="{uid}" clipPathUnits="userSpaceOnUse"><rect width="63" height="16"/></clipPath></defs><g clip-path="url(#{uid})">'+''.join(sv)+'</g>'

def text(c,x,y,s,size=8):
 c.setFillColor(HexColor('#243038'));c.setFont(FONTNAME,size);c.drawString(x*mm,A4[1]-y*mm,s)
def marks(c,x,y):
 c.setStrokeColor(HexColor('#aaaaaa'));c.setLineWidth(.25)
 for xx in (x,x+63*mm):
  for yy in (y,y+16*mm):
   dx=-1 if xx==x else 1;dy=-1 if yy==y else 1
   c.line(xx+dx*.5*mm,yy,xx+dx*1.6*mm,yy);c.line(xx,yy+dy*.5*mm,xx,yy+dy*1.6*mm)

def main():
 for old in OUT.glob('n64-end-labels-padronizadas-*.svg'):old.unlink()
 c=canvas.Canvas(str(OUT/'n64-end-labels-padronizadas-A4.pdf'),pagesize=A4)
 c.setTitle('N64 Open Labels | Integrated layout 2.0')
 for page in range(math.ceil(len(items)/18)):
  text(c,20,16,'N64 / END LABELS',15)
  text(c,20,24,'Integrated layout 2.0  •  63 × 16 mm  •  A4 / 100%',8)
  sv=[]
  for k,item in enumerate(items[page*18:(page+1)*18]):
   x=28+(k%2)*91;top=34+(k//2)*25;y=A4[1]-(top+16)*mm
   v=label(c,item,x*mm,y);marks(c,x*mm,y)
   text(c,x,top+20,item['name'],6)
   sv.append(f'<g id="label-{page*18+k:02}" aria-label="{html.escape(item["name"])}" transform="translate({x},{top})">{v}</g>')
  c.setStrokeColor(HexColor('#333333'));c.setLineWidth(.5);c.line(28*mm,24*mm,78*mm,24*mm)
  for j in range(11):c.line((28+j*5)*mm,24*mm,(28+j*5)*mm,(26 if j%2==0 else 25)*mm)
  text(c,28,278,'Conferência: 50 mm',7);text(c,119,272,'Tamanho real. Não ajustar à página.',7);text(c,119,278,'Teste o encaixe em papel comum.',7)
  (OUT/f'n64-end-labels-padronizadas-{page+1:02}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="210mm" height="297mm" viewBox="0 0 210 297">'+''.join(sv)+'</svg>')
  c.showPage()
 c.save()
 # Large proofs are explicitly not printing size.
 c=canvas.Canvas(str(OUT/'prova-ampliada.pdf'),pagesize=A4)
 for i,it in enumerate(items):
  top=20+(i%6)*44;text(c,20,top-3,it['name'],8)
  label(c,it,20*mm,A4[1]-(top+38)*mm,149.625*mm,38*mm)
  if i%6==5 or i==len(items)-1:c.showPage()
 c.save()
 print(f"Built {len(items)} labels in {OUT}")

if __name__=='__main__':
 parser=argparse.ArgumentParser(description='Print integrated N64 end labels at 63 x 16 mm')
 parser.add_argument('--config',type=Path,default=ROOT/'examples/demo.json')
 parser.add_argument('--output',type=Path,default=OUT)
 parser.add_argument('--select',help='Comma-separated zero-based recipe indexes, e.g. 0,3,5')
 args=parser.parse_args()
 try:
  items=load_items(args.config)
  if args.select:
   indexes=[int(n) for n in args.select.split(',')]
   if len(set(indexes))!=len(indexes) or any(n<0 or n>=len(items) for n in indexes):
    raise ValueError('Selection must contain unique indexes within the recipe range')
   items=[items[n] for n in indexes]
  OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
  main()
 except (ValueError,KeyError,FileNotFoundError) as exc:
  parser.exit(2,f'Error: {exc}\n')
