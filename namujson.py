# 모듈 임포트
import json
import os
import pickle
import urllib.parse
import sqlite3
import re

json_data = open('set.json').read()
set_data = json.loads(json_data)

conn = sqlite3.connect(set_data['db'] + '.db')
curs = conn.cursor()

# 숫자 판단
def isNumber(data):
  try:
    tmp1 = float(data)
    
    return(True)
  except ValueError:
    return(False)

# 편집자를 구분하는 부분입니다. 리그베다 위키 유저는 R:로, 나무위키 유저는 N:의 Prefix가 붙습니다.
def editorProcess(editor):
    if(editor.find("R : ") != -1 or isNumber(editor) == True):
        pass
    else:
        editor = "N : " + editor
    
    return(editor)
    
def mainprocess(dictdata):
    revision = 0
    revisionNum = 0
    editTime = 'Dump'
    Errorlist = []

    # 이하의 코드는 문서별로 실행됩니다.
    for i in range(len(dictdata)):
        # 데이터를 읽어서 본문, 문서 제목, 리비전 수를 셉니다.
        print(i)
        
        revision = len(dictdata[i]['contributors'])
        namespace = str(dictdata[i]['namespace'])
        
        if(namespace == '0' or namespace == '1'):
            if(namespace == '1'):
                text = re.sub("\[\[분류:(?P<in>(?:(?!]]).)*)]]", "{{{#!noin [[분류:\g<in>]]}}}", str(dictdata[i]['text']))
                title = '틀:' + str(dictdata[i]['title'])
            else:
                text = str(dictdata[i]['text'])
                title = str(dictdata[i]['title'])
                
            # SQL에 삽입 합니다.
            try:
                curs.execute("insert into data (title, data, acl) values (?, ?, '')", [title, text])
            except:
                Errorlist.append(title)
                
            # 이하의 코드는 리비전별로 실행됩니다.
            for x in range(revision):      
                revisionNum = x+1
                # 편집자 기록을 만듭니다.
                editor = dictdata[i]['contributors'][x]
                editor = editorProcess(editor)
                try:
                    curs.execute("insert into history (id, title, data, date, ip, send, leng) values (?, ?, '', ?, ?, '', '0')", [str(revisionNum), title, editTime, editor])
                except:
                    Errorlist.append(title)
            
    print("문서 변환 작업이 종료되었습니다.")
    print(str(len(dictdata)) + "개의 문서가 데이터에 존재합니다. 그 중 " + str((len(dictdata) - len(Errorlist))) + "개의 문서가 변환되었습니다. 오류가 발생한 문서는 " + str(len(Errorlist)) + " 개 입니다.")

print("이 스크립트는 나무위키 JSON 데이터가 필요합니다. 데이터를 로딩합니다.")

jsondata = os.path.join('namuwikidata.json')
namuwikidata = open(jsondata,'r')
print("JSON 데이터 읽기 완료")

dictdata = json.load(namuwikidata)
namuwikidata.close()
print("JSON 데이터 사전형으로 변환 완료")
    
print("모든 사전 작업이 종료되었습니다. 변환을 시작합니다.")
mainprocess(dictdata)
conn.commit()