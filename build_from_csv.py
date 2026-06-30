#!/usr/bin/env python3
"""Notion CSV -> AI 반사사전 official JSON.
현재 원본 CSV와 권장 확장 CSV 헤더를 모두 지원합니다.
"""
import argparse,csv,json,re
from datetime import datetime,timezone
from pathlib import Path

def split(v): return [x.strip() for x in re.split(r'[,;\n]',v or '') if x.strip()]
def get(row,*names):
    for n in names:
        if row.get(n): return row[n].strip()
    return ''
def main():
    p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('-o','--output',default='public/glossary.json');p.add_argument('--version',default=datetime.now().strftime('%Y.%m.%d.%H%M'));p.add_argument('--include-drafts',action='store_true');a=p.parse_args()
    rows=list(csv.DictReader(open(a.csv,encoding='utf-8-sig',newline=''))); entries=[]
    for i,r in enumerate(rows,1):
        status=get(r,'상태','Status') or 'published'
        if not a.include_drafts and status not in {'published','공개','검수 완료'}: continue
        aliases=split(get(r,'약어·별칭','Aliases','약어'))
        full=get(r,'풀네임','Full name','Term')
        korean=get(r,'한국어 이름','Korean')
        key=(aliases[0] if aliases else korean or full)
        if not key: continue
        entries.append({
            'id':get(r,'ID') or i,
            'key':key,
            'aliases':aliases,
            'full':full or key,
            'korean':korean,
            'searchTerms':split(get(r,'검색 키워드','Search terms','Search Terms','Synonyms','영문 검색어')),
            'oneLine':get(r,'1초 설명','Definition'),
            'definition':get(r,'상세 설명','Definition'),
            'categories':split(get(r,'분류','Class1'))+split(get(r,'Class2')),
            'source':get(r,'원문 링크','Source'),
            'status':'published',
            'stability':get(r,'안정도','Stability') or 'unreviewed',
            'lastReviewed':get(r,'마지막 검수일','Last reviewed'),
            'detect':(get(r,'자동 감지','Detect').lower() not in {'false','0','아니오','no'}),
            'interviewAnswer':get(r,'면접 답변','Interview answer')
        })
    data={'schemaVersion':1,'version':a.version,'publishedAt':datetime.now(timezone.utc).isoformat(),'releaseNotes':[], 'entries':entries}
    o=Path(a.output);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(f'{len(entries)}개 항목 -> {o}')
if __name__=='__main__':main()
