#!/usr/bin/env python3
"""Notion data source -> 반사사전 JSON.
환경 변수: NOTION_TOKEN, NOTION_DATA_SOURCE_ID
선택: OUTPUT_PATH, GLOSSARY_VERSION
"""
import json, os, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN=os.environ['NOTION_TOKEN']
DATA_SOURCE_ID=os.environ['NOTION_DATA_SOURCE_ID']
OUT=Path(os.environ.get('OUTPUT_PATH','public/glossary.json'))
VERSION=os.environ.get('GLOSSARY_VERSION',datetime.now().strftime('%Y.%m.%d.%H%M'))
API='https://api.notion.com/v1'
HEADERS={'Authorization':f'Bearer {TOKEN}','Notion-Version':'2026-03-11','Content-Type':'application/json'}

def request(path, body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(API+path,data=data,headers=HEADERS,method='GET' if body is None else 'POST')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def text_parts(parts): return ''.join(x.get('plain_text','') for x in (parts or [])).strip()
def value(p):
    if not p:return ''
    t=p.get('type')
    if t in ('title','rich_text'):return text_parts(p.get(t))
    if t in ('select','status'):return (p.get(t) or {}).get('name','')
    if t=='multi_select':return ', '.join(x.get('name','') for x in p.get(t,[]))
    if t=='date':return (p.get('date') or {}).get('start','')
    if t=='checkbox':return 'true' if p.get('checkbox') else 'false'
    if t in ('url','email','phone_number','number'):return p.get(t) or ''
    if t=='formula':
        f=p.get('formula') or {};return f.get(f.get('type'),'')
    return ''
def get(props,*names):
    for n in names:
        if n in props:
            v=value(props[n])
            if v is not None and str(v).strip():return str(v).strip()
    return ''
def split(s): return [x.strip() for x in str(s or '').replace(';',',').split(',') if x.strip()]
def uniq(items):
    out=[];seen=set()
    for item in items:
        v=' '.join(str(item or '').split()).strip();k=v.casefold()
        if v and k not in seen:seen.add(k);out.append(v)
    return out

def split_bilingual(term):
    """Transformer (트랜스포머) -> ('Transformer', '트랜스포머').
    마지막 괄호 안에 한글이 있을 때만 분리해 일반 영문 괄호 표기를 훼손하지 않습니다.
    """
    raw=' '.join(str(term or '').split()).strip()
    m=re.match(r'^(.*?)\s*\(([^()]*(?:[가-힣])[^()]*)\)\s*$',raw)
    if not m:return raw,''
    return m.group(1).strip(),m.group(2).strip()

def normalize_aliases(values):
    out=[]
    for item in values:
        base,ko=split_bilingual(item)
        out.extend([base,ko])
    return uniq(out)

def main():
    pages=[]; cursor=None
    while True:
        body={'page_size':100}
        if cursor:body['start_cursor']=cursor
        res=request(f'/data_sources/{DATA_SOURCE_ID}/query',body);pages+=res.get('results',[])
        if not res.get('has_more'):break
        cursor=res.get('next_cursor')
    entries=[]
    for page in pages:
        props=page.get('properties',{})
        status=get(props,'상태','Status') or 'published'
        if status not in {'published','공개','검수 완료'}:continue

        raw_term=get(props,'풀네임','Full name','Term')
        full_from_term,korean_from_term=split_bilingual(raw_term)
        aliases=normalize_aliases(split(get(props,'약어·별칭','Aliases','약어')))
        explicit_korean=get(props,'한국어 이름','Korean')
        korean=explicit_korean or korean_from_term
        full=full_from_term or raw_term
        key=aliases[0] if aliases else full
        if not key:continue

        # 괄호 병기에서 분리된 한글명도 별칭으로 보존해 한글 감지가 가능하게 합니다.
        aliases=uniq(aliases+([korean] if korean else []))
        aliases=[a for a in aliases if a.casefold()!=key.casefold()]

        entries.append({
            'id':page.get('id'),
            'key':key,
            'aliases':aliases,
            'full':full or key,
            'korean':korean,
            'searchTerms':split(get(props,'검색 키워드','Search terms','Search Terms','Synonyms','영문 검색어')),
            'oneLine':get(props,'1초 설명','Definition'),
            'definition':get(props,'상세 설명','Definition'),
            'categories':split(get(props,'분류','Class1'))+split(get(props,'Class2')),
            'source':get(props,'원문 링크','Source') or page.get('url',''),
            'status':'published',
            'stability':get(props,'안정도','Stability') or 'unreviewed',
            'lastReviewed':get(props,'마지막 검수일','Last reviewed'),
            'detect':get(props,'자동 감지','Detect').lower() not in {'false','0','아니오','no'},
            'interviewAnswer':get(props,'면접 답변','Interview answer')
        })
    data={'schemaVersion':1,'version':VERSION,'publishedAt':datetime.now(timezone.utc).isoformat(),'releaseNotes':['영문명 (한글명) 자동 분리 및 감지 개선'], 'entries':entries}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(entries)}개 공개 항목 -> {OUT}')
if __name__=='__main__':main()
