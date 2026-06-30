#!/usr/bin/env python3
"""사전의 검색 누락 가능성을 검사합니다."""
import argparse,json,re
from collections import Counter

def main():
    ap=argparse.ArgumentParser();ap.add_argument('json_file');args=ap.parse_args()
    data=json.load(open(args.json_file,encoding='utf-8'))
    entries=data.get('entries',[]);issues=[]
    keys=Counter(str(e.get('key','')).casefold() for e in entries)
    for e in entries:
        ident=e.get('id',e.get('key'))
        full=str(e.get('full','')).strip();ko=str(e.get('korean','')).strip();key=str(e.get('key','')).strip()
        if not full: issues.append((ident,'풀네임 누락',key))
        if '이름 보강 필요' in (key+full): issues.append((ident,'임시 이름',key))
        if full==ko and re.search(r'[가-힣]',full): issues.append((ident,'영어 이름 누락 가능성',key))
        if keys[key.casefold()]>1: issues.append((ident,'중복 표시어',key))
    if not issues:
        print('문제 후보가 없습니다.');return
    for ident,kind,key in issues:print(f'[{kind}] {ident}: {key}')
    print(f'총 {len(issues)}건')
if __name__=='__main__':main()
