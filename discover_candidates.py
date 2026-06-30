#!/usr/bin/env python3
"""Configured public feeds/pages에서 미등록 AI 용어 후보를 수집합니다.
후보만 생성하며 공식 glossary에는 절대 자동 병합하지 않습니다.
"""
import argparse, collections, html, json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA='AI-Reflex-Glossary-Candidate-Collector/1.0'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/rss+xml, application/atom+xml, text/html, */*'})
    with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode(r.headers.get_content_charset() or 'utf-8','replace')
def clean(s):
    s=re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s)).strip()
def documents(raw,kind):
    if kind=='html':return [clean(raw)]
    try:
        root=ET.fromstring(raw); out=[]
        for node in root.findall('.//item')+root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            parts=[]
            for tag in ('title','description','summary','content'):
                for x in node.findall('.//'+tag)+node.findall('.//{http://www.w3.org/2005/Atom}'+tag):parts.append(''.join(x.itertext()))
            if parts:out.append(clean(' '.join(parts)))
        return out or [clean(raw)]
    except ET.ParseError:return [clean(raw)]
def known_terms(glossary):
    d=json.load(open(glossary,encoding='utf-8')); known=set()
    for e in d.get('entries',[]):
        for x in [e.get('key'),e.get('full'),*(e.get('aliases') or [])]:
            if x:known.add(str(x).casefold())
    return known

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources',default='sources.json');ap.add_argument('--glossary',default='public/glossary.json');ap.add_argument('-o','--output',default='review/candidates.json');a=ap.parse_args()
    sources=json.load(open(a.sources,encoding='utf-8')); known=known_terms(a.glossary); hits=collections.defaultdict(lambda:{'count':0,'expansions':set(),'sources':set(),'contexts':[]})
    pair1=re.compile(r'\b([A-Z][A-Za-z0-9-]+(?:\s+[A-Z][A-Za-z0-9-]+){1,8})\s*\(([A-Z][A-Z0-9-]{1,10})\)')
    pair2=re.compile(r'\b([A-Z][A-Z0-9-]{1,10})\s*\(([A-Za-z][^()\n]{4,100})\)')
    standalone=re.compile(r'\b(?:[A-Z][A-Z0-9-]{2,9}|[A-Z][a-z]+[A-Z][A-Za-z0-9]{2,})\b')
    for src in sources:
        try: docs=documents(fetch(src['url']),src.get('type','rss'))
        except Exception as e:
            print(f"WARN {src.get('name',src['url'])}: {e}");continue
        for text in docs:
            for full,abbr in pair1.findall(text):
                if abbr.casefold() not in known:
                    h=hits[abbr];h['count']+=1;h['expansions'].add(full);h['sources'].add(src['url']);h['contexts'].append(text[:280])
            for abbr,full in pair2.findall(text):
                if abbr.casefold() not in known:
                    h=hits[abbr];h['count']+=1;h['expansions'].add(full.strip());h['sources'].add(src['url']);h['contexts'].append(text[:280])
            for term in standalone.findall(text):
                if term.casefold() not in known:
                    h=hits[term];h['count']+=1;h['sources'].add(src['url']);h['contexts'].append(text[:280])
    candidates=[]
    for term,h in sorted(hits.items(),key=lambda kv:(-kv[1]['count'],kv[0])):
        candidates.append({'term':term,'possibleExpansions':sorted(h['expansions']),'observations':h['count'],'sources':sorted(h['sources']),'contexts':h['contexts'][:3],'status':'candidate','observedAt':datetime.now(timezone.utc).isoformat()})
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'generatedAt':datetime.now(timezone.utc).isoformat(),'candidates':candidates},ensure_ascii=False,indent=2),encoding='utf-8');print(f'{len(candidates)}개 후보 -> {out}')
if __name__=='__main__':main()
