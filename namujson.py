# 모듈 임포트
import json
import os
import pickle
import urllib.parse
import sqlite3
import pickle
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
    revisionNum = 0
    editTime = ''
    x = 0

    for d_dict in dictdata:
        print(x + 1)
        x += 1
        namespace = str(d_dict['namespace'])
        if(namespace == '0' or namespace == '1'):
            if(namespace == '1'):
                text = re.sub("\[\[분류:(?P<in>(?:(?!]]).)*)]]", "{{{#!noin [[분류:\g<in>]]}}}", str(d_dict['text']))
                title = '틀:' + str(d_dict['title'])
            else:
                text = str(d_dict['text'])
                title = str(d_dict['title'])

            r_pas = re.compile('(http(?:s)?:\/\/(?:(?:(?!(?:\.(?:[Pp][Nn][Gg]|[Gg][Ii][Ff]|[Jj][Pp][Gg]|[Jj][Pp][Ee][Gg]|[Ww][Ee][Bb][Pp])| |]])).)*))(\.(?:[Pp][Nn][Gg]|[Gg][Ii][Ff]|[Jj][Pp][Gg]|[Jj][Pp][Ee][Gg]|[Ww][Ee][Bb][Pp]))((?:(?:\?|&)[^ \n\]|]*)+)?')
            image = r_pas.findall(text)
            for i_data in image:
                try:
                    try:
                        plus = re.sub('\?', '|', i_data[2])
                    except:
                        plus = ''

                    h = re.sub('\.(?P<in>[Pp][Nn][Gg]|[Gg][Ii][Ff]|[Jj][Pp][Gg]|[Jj][Pp][Ee][Gg]|[Ww][Ee][Bb][Pp])', '#\g<in>#', i_data[1])
                        
                    r_i_data = '[[외부:' + i_data[0] + h + plus + ']]'
                    text = r_pas.sub(r_i_data, text, 1)
                except:
                    text = r_pas.sub('', text, 1)

            text = re.sub('#(?P<in>[Pp][Nn][Gg]|[Gg][Ii][Ff]|[Jj][Pp][Gg]|[Jj][Pp][Ee][Gg]|[Ww][Ee][Bb][Pp])#', '.\g<in>', text)
                
            curs.execute("insert into data (title, data, acl) values (?, ?, '')", [title, text])

            revision = len(d_dict['contributors'])
            for y in range(revision):
                revisionNum = y + 1
                editor = d_dict['contributors'][y]
                editor = editorProcess(editor)

                curs.execute("insert into history (id, title, data, date, ip, send, leng) values (?, ?, '', ?, ?, '', '0')", [str(revisionNum), title, editTime, editor])
            
    print("문서 변환 작업이 종료되었습니다.")

print("이 스크립트는 나무위키 JSON 데이터가 필요합니다. 데이터를 로딩합니다.")
if(os.path.exists(os.path.join("rawdata.pickle")) != True):
    jsondata = os.path.join('namuwikidata.json')
    namuwikidata = open(jsondata,'r')
    print("JSON 데이터 읽기 완료")

    dictdata = json.load(namuwikidata)
    namuwikidata.close()
    print("JSON 데이터 사전형으로 변환 완료")

    tempdata = open('rawdata.pickle', 'wb')
    pickle.dump(dictdata,tempdata)
    print("다음 실행을 위해서 임시 데이터를 저장합니다.")

rawdata_address = r"rawdata.pickle"
rawdata = open(os.path.join(rawdata_address),'rb')
dictdata = pickle.load(rawdata)
rawdata.close()
    
print("모든 사전 작업이 종료되었습니다. 변환을 시작합니다.")
mainprocess(dictdata)
conn.commit()