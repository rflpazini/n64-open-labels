import importlib.util,json,subprocess,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class GeneratorTests(unittest.TestCase):
 def test_nineteenth_label_goes_to_second_page(self):
  m=module('renderer',ROOT/'build.py');base=json.loads((ROOT/'examples/demo.json').read_text())[0]
  with tempfile.TemporaryDirectory() as t:
   m.OUT=Path(t);m.items=[dict(base,name=f'Test {i}') for i in range(19)];m.main()
   p=PdfReader(m.OUT/'n64-end-labels-padronizadas-A4.pdf')
   self.assertEqual(len(p.pages),2);self.assertAlmostEqual(float(p.pages[0].mediabox.width),595.2756,places=3)
   self.assertIn('Test 18',p.pages[1].extract_text());self.assertNotIn('Test 17',p.pages[1].extract_text())
   svg=ET.parse(m.OUT/'n64-end-labels-padronizadas-02.svg')
   images=svg.findall('.//{http://www.w3.org/2000/svg}image')
   self.assertEqual(len(images),2)
   for im in images:self.assertTrue(im.get('{http://www.w3.org/1999/xlink}href').startswith('data:image/png;base64,'))
 def test_invalid_selection_fails_without_output(self):
  with tempfile.TemporaryDirectory() as t:
   r=subprocess.run([sys.executable,str(ROOT/'build.py'),'--select','-1','--output',t],capture_output=True,text=True)
   self.assertEqual(r.returncode,2);self.assertFalse(list(Path(t).glob('*.pdf')))
 def test_missing_art_has_actionable_error(self):
  r=subprocess.run([sys.executable,str(ROOT/'build.py'),'--config',str(ROOT/'examples/collection-18.json')],capture_output=True,text=True)
  self.assertEqual(r.returncode,2);self.assertIn('Missing asset',r.stderr);self.assertIn('ASSETS.md',r.stderr)
class CatalogTests(unittest.TestCase):
 def test_revision_dedup_preserves_region_and_excludes_prototype(self):
  m=module('importer',ROOT/'scripts/import_catalog.py')
  names=['Example (USA)','Example (USA) (Rev 1)','Example (Japan)','Example (USA) (Proto)']
  raw='\n'.join('game (\n name "'+n+'"\n)\n' for n in names)
  rows,excluded=m.parse(raw)
  self.assertEqual(len(rows),2);self.assertEqual({r['region'] for r in rows},{'USA','Japan'});self.assertEqual(len(excluded),1)
class AToZTests(unittest.TestCase):
 def test_letter_groups_digits_together(self):
  m=module('atoz',ROOT/'scripts/export_a_to_z.py')
  self.assertEqual([m.letter(n) for n in ('007 - The World Is Not Enough','1080 Snowboarding','banjo-Tooie','Yoshi')],['0-9','0-9','B','Y'])
if __name__=='__main__':unittest.main()
