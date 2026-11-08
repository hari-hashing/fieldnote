#!/usr/bin/env python3
import json,subprocess,sys
import xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(n):return json.loads((R/n).read_text(encoding='utf-8'))
def main():
 bins=load('data/taxonomy.json');db=load('data/papers.json');ideas=load('data/opportunities.json');manifest=load('data/manifest.json')
 assert len(bins)==11 and len({x['id'] for x in bins})==11
 papers=db if isinstance(db,list) else db.get('papers',[]);ids=set();valid={x['id'] for x in bins}
 for p in papers:
  assert p.get('title');key=str(p.get('id') or p['title']);assert key not in ids;ids.add(key)
  assert not p.get('primary_bin') or p['primary_bin'] in valid
 assert isinstance(ideas.get('opportunities',[]),list);assert isinstance(manifest.get('archives',[]),list)
 html=(R/'index.html').read_text(encoding='utf-8')
 for term in ('canonical','application/ld+json','newsletter-form','theme-select','font-select'):assert term in html,term
 subprocess.run([sys.executable,str(R/'scripts/build_site.py')],check=True)
 for f in ('index.html','privacy.html','robots.txt','sitemap.xml','feed.xml','assets/preferences.js','assets/newsletter.js','data/papers.json','papers'):
  assert (R/'_site'/f).exists(),f
 ET.parse(R/'_site'/'sitemap.xml');feed_tree=ET.parse(R/'_site'/'feed.xml')
 for item in feed_tree.getroot().findall('{http://www.w3.org/2005/Atom}entry'):
  updated=item.find('{http://www.w3.org/2005/Atom}updated').text
  assert 'T' in updated and updated.endswith('Z'), 'Atom updated timestamps must be RFC3339 UTC date-times'
 assert len(list((R/'_site'/'papers').glob('*/index.html'))) == len(papers), 'One indexable page should be built per paper'
 workflow=(R/'.github/workflows/research-atlas.yml').read_text(encoding='utf-8')
 assert 'pull_request:' in workflow and 'actions/deploy-pages@v4' in workflow and "github.event.pull_request.head.sha || 'main'" in workflow
 worker=(R/'newsletter/worker.js').read_text(encoding='utf-8')
 for endpoint in ("'/subscribe'", "'/verify'", "'/unsubscribe'", "'/health'"): assert endpoint in worker
 assert 'Idempotency-Key' in worker and 'WORKER_URL' in worker
 print(f'OK: {len(bins)} bins, {len(papers)} papers, {len(ideas.get("opportunities",[]))} opportunities')
if __name__=='__main__':main()
