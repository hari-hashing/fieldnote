#!/usr/bin/env python3
"""Build Fieldnote's crawlable static site and per-paper landing pages."""
from pathlib import Path
import datetime as dt, html, json, os, re, shutil, hashlib
from xml.etree.ElementTree import Element, SubElement, ElementTree
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'_site'
SITE=os.environ.get('FIELDNOTE_SITE_URL','https://hari-hashing.github.io/fieldnote').rstrip('/')
def read(path,default):
 try:return json.loads(path.read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError):return default
def slug(s):return (re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:78].strip('-') or 'paper')
def atom_time(value):
 value=str(value or '').strip()
 if not value:return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
 try:
  parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
  if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=dt.timezone.utc)
  return parsed.astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
 except ValueError:return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
def paper_html(p,canonical):
 title=str(p.get('title') or 'Research paper'); abstract=str(p.get('abstract') or p.get('contribution') or 'Abstract not indexed.')
 authors=str(p.get('authors') or 'Authors not indexed'); paper_url=str(p.get('paper_url') or SITE)
 data={'@context':'https://schema.org','@type':'ScholarlyArticle','headline':title,'author':[{'@type':'Person','name':x.strip()} for x in authors.split(',') if x.strip()],'datePublished':p.get('first_published') or None,'url':canonical,'sameAs':paper_url,'description':abstract[:500],'isAccessibleForFree':True}
 esc=lambda x:html.escape(str(x),quote=True)
 code=p.get('code_url'); code_link=f'<p><a href="{esc(code)}" rel="nofollow">Official code/project ↗</a></p>' if code else ''
 return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Fieldnote</title><meta name="description" content="{esc(abstract[:300])}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="../../assets/styles.css"><script type="application/ld+json">{json.dumps(data,ensure_ascii=False).replace('<','\\\\u003c')}</script></head><body><main style="max-width:900px;margin:8vh auto;padding:24px"><p><a href="../../">← Fieldnote Research Atlas</a></p><p class="eyebrow">RESEARCH PAPER · {esc(p.get('first_published',''))}</p><h1>{esc(title)}</h1><p>{esc(authors)}</p><p>{esc(p.get('venue','Venue not verified'))}</p><h2>Abstract / indexed summary</h2><p style="line-height:1.85">{esc(abstract)}</p><p><a href="{esc(paper_url)}" rel="nofollow">Open primary paper source ↗</a></p>{code_link}<p>Research classification: {esc(p.get('primary_bin','Unclassified'))}</p></main></body></html>"""
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for name in ('index.html','privacy.html','robots.txt','README.md','LICENSE'):
 if (ROOT/name).exists():shutil.copy2(ROOT/name,OUT/name)
for name in ('assets','docs'):
 if (ROOT/name).exists():shutil.copytree(ROOT/name,OUT/name)
dataout=OUT/'data';dataout.mkdir()
for name in ('taxonomy.json','papers.json','opportunities.json','manifest.json'):
 shutil.copy2(ROOT/'data'/name,dataout/name)
if (ROOT/'data'/'archives').exists():shutil.copytree(ROOT/'data'/'archives',dataout/'archives')
pdb=read(ROOT/'data'/'papers.json',{'papers':[]});papers=pdb if isinstance(pdb,list) else pdb.get('papers',[]);stamp=pdb.get('generated_at','') if isinstance(pdb,dict) else ''
urls=[SITE+'/',SITE+'/privacy.html'];seen=set();feeditems=[]
for p in sorted(papers,key=lambda x:str(x.get('first_published') or ''),reverse=True):
 title=str(p.get('title') or '').strip();pid=str(p.get('id') or title)
 if not title or pid in seen:continue
 seen.add(pid);suffix=hashlib.sha256(pid.encode('utf-8')).hexdigest()[:10];slugid=slug(title)[:64].rstrip('-')+'-'+suffix;url=SITE+'/papers/'+slugid+'/'
 dest=OUT/'papers'/slugid;dest.mkdir(parents=True,exist_ok=True);(dest/'index.html').write_text(paper_html(p,url),encoding='utf-8');urls.append(url)
 if len(feeditems)<50:feeditems.append(p)
root=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for u in urls:
 n=SubElement(root,'url');SubElement(n,'loc').text=u
 if stamp:SubElement(n,'lastmod').text=stamp[:10]
ElementTree(root).write(OUT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
feed=Element('feed',xmlns='http://www.w3.org/2005/Atom');SubElement(feed,'title').text='Fieldnote — Embodied AI Research Atlas';SubElement(feed,'id').text=SITE+'/';SubElement(feed,'updated').text=stamp or dt.datetime.now(dt.timezone.utc).isoformat();SubElement(feed,'link',href=SITE+'/feed.xml',rel='self',type='application/atom+xml');SubElement(feed,'link',href=SITE+'/')
for p in feeditems:
 e=SubElement(feed,'entry');SubElement(e,'title').text=str(p.get('title') or 'Research paper');SubElement(e,'id').text=str(p.get('paper_url') or p.get('id') or '');SubElement(e,'link',href=str(p.get('paper_url') or SITE));SubElement(e,'updated').text=atom_time(p.get('latest_revision') or p.get('first_published') or stamp);SubElement(e,'summary').text=str(p.get('abstract') or '')[:1600]
ElementTree(feed).write(OUT/'feed.xml',encoding='utf-8',xml_declaration=True)
(OUT/'.nojekyll').write_text('',encoding='utf-8');print(f'Built {len(papers)} indexed paper pages and {len(urls)} sitemap URLs in {OUT}')
