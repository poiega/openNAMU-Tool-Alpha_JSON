# 모듈 임포트
import json
import os
import pickle
import urllib.parse
import pymysql
import sqlite3
import threading
import pickle
import re

# DB
while 1:
    try:
        set_data = json.loads(open('data/set.json').read())
        if not 'db_type' in set_data:
            try:
                os.remove('data/set.json')
            except:
                print('Please delete set.json')
                print('----')
                raise
        else:
            break
    except:
        if os.getenv('NAMU_DB') != None or os.getenv('NAMU_DB_TYPE') != None:
            set_data = { 
                "db" : os.getenv('NAMU_DB') if os.getenv('NAMU_DB') else 'data', 
                "db_type" : os.getenv('NAMU_DB_TYPE') if os.getenv('NAMU_DB_TYPE') else 'sqlite'
            }

            break
        else:        
            new_json = ['', '']
            normal_db_type = ['sqlite', 'mysql']

            print('DB type (sqlite, mysql) : ', end = '')
            new_json[0] = str(input())
            if new_json[0] == '' or not new_json[0] in normal_db_type:
                new_json[0] = 'sqlite'

            all_src = []
            for i_data in os.listdir("."):
                f_src = re.search("(.+)\.db$", i_data)
                if f_src:
                    all_src += [f_src.groups()[0]]

            if all_src != []:
                print('DB name (' + ', '.join(all_src) + ') : ', end = '')
            else:
                print('DB name (data) : ', end = '')

            new_json[1] = str(input())
            if new_json[1] == '':
                new_json[1] = 'data'
                
            with open('data/set.json', 'w') as f:
                f.write('{ "db" : "' + new_json[1] + '", "db_type" : "' + new_json[0] + '" }')
                
            set_data = json.loads(open('data/set.json').read())
            
            break
        
print('DB name : ' + set_data['db'])
print('DB type : ' + set_data['db_type'])

def db_change(data):
    if set_data['db_type'] == 'mysql':
        data = data.replace('random()', 'rand()')
        data = data.replace('%', '%%')
        data = data.replace('?', '%s')

    return data

if set_data['db_type'] == 'mysql':
    try:
        set_data_mysql = json.loads(open('data/mysql.json').read())
    except:
        new_json = ['', '']

        while 1:
            print('DB user id : ', end = '')
            new_json[0] = str(input())
            if new_json[0] != '':
                break

        while 1:
            print('DB password : ', end = '')
            new_json[1] = str(input())
            if new_json[1] != '':
                break

        with open('data/mysql.json', 'w') as f:
            f.write('{ "user" : "' + new_json[0] + '", "password" : "' + new_json[1] + '" }')
                
        set_data_mysql = json.loads(open('data/mysql.json').read())

    conn = pymysql.connect(
        host = 'localhost', 
        user = set_data_mysql['user'], 
        password = set_data_mysql['password'],
        charset = 'utf8mb4'
    )
    curs = conn.cursor()

    try:
        curs.execute(db_change('create database ? default character set utf8mb4;')%pymysql.escape_string(set_data['db']))
    except:
        pass

    curs.execute(db_change('use ?')%pymysql.escape_string(set_data['db']))
else:
    conn = sqlite3.connect(set_data['db'] + '.db', check_same_thread = False)
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
    if editor.find("R:") != -1 or isNumber(editor) == True:
        pass
    else:
        editor = "N:" + editor
    
    return(editor)
    
def mainprocess(dictdata):
    revisionNum = 0
    editTime = ''
    x = 0
    for d_dict in dictdata:        
        x += 1
        if x % 100 == 0:
            print(x)
        
        namespace = str(d_dict['namespace'])
        if namespace == '0' or namespace == '1':
            if namespace == '1':
                text = str(d_dict['text'])
                title = '틀:' + str(d_dict['title'])
            else:
                text = str(d_dict['text'])
                title = str(d_dict['title'])
                
            curs.execute(db_change("insert into data (title, data) values (?, ?)"), [title, text])

            if x == 0:
                break

            revision = len(d_dict['contributors'])
            for y in range(revision):
                revisionNum = y + 1
                
                editor = d_dict['contributors'][y]
                editor = editorProcess(editor)

                curs.execute(db_change("insert into history (id, title, data, date, ip, send, leng, hide) values (?, ?, ?, ?, ?, '', '0', '')"), [
                    str(revisionNum), 
                    title, 
                    text if y == revision else '', 
                    editTime, 
                    editor
                ])

    curs.execute(db_change('delete from other where name = "count_all_title"'))
    curs.execute(db_change('insert into other (name, data) values ("count_all_title", ?)'), [str(x)])
    
    print("문서 변환 작업이 종료되었습니다.")

print("이 스크립트는 나무위키 JSON 데이터가 필요합니다. 데이터를 로딩합니다.")
if os.path.exists(os.path.join("rawdata.pickle")) != True:
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
rawdata = open(os.path.join(rawdata_address), 'rb')
dictdata = pickle.load(rawdata)
rawdata.close()
    
print("모든 사전 작업이 종료되었습니다. 변환을 시작합니다.")
mainprocess(dictdata)
conn.commit()