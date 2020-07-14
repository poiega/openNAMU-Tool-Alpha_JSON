# 모듈 임포트
import json
import os
import urllib.parse
import datetime
import pymysql
import sqlite3
import threading
import pickle
import re

# DB
while 1:
    try:
        set_data = json.loads(open('data/set.json', encoding='utf8').read())
        if not 'db_type' in set_data:
            try:
                os.remove('data/set.json')
            except:
                print('Please delete set.json')
                print('----')
                raise
        else:
            print('DB name : ' + set_data['db'])
            print('DB type : ' + set_data['db_type'])

            break
    except:
        if os.getenv('NAMU_DB') != None or os.getenv('NAMU_DB_TYPE') != None:
            set_data = {
                "db" : os.getenv('NAMU_DB') if os.getenv('NAMU_DB') else 'data',
                "db_type" : os.getenv('NAMU_DB_TYPE') if os.getenv('NAMU_DB_TYPE') else 'sqlite'
            }

            print('DB name : ' + set_data['db'])
            print('DB type : ' + set_data['db_type'])

            break
        else:
            new_json = ['', '']
            normal_db_type = ['sqlite', 'mysql']

            print('DB type (sqlite) [sqlite, mysql] : ', end = '')
            new_json[0] = str(input())
            if new_json[0] == '' or not new_json[0] in normal_db_type:
                new_json[0] = 'sqlite'

            all_src = []
            for i_data in os.listdir("."):
                f_src = re.search(r"(.+)\.db$", i_data)
                if f_src:
                    all_src += [f_src.group(1)]

            if all_src != [] and new_json[0] != 'mysql':
                print('DB name (data) [' + ', '.join(all_src) + '] : ', end = '')
            else:
                print('DB name (data) : ', end = '')

            new_json[1] = str(input())
            if new_json[1] == '':
                new_json[1] = 'data'

            with open('data/set.json', 'w', encoding='utf8') as f:
                f.write('{ "db" : "' + new_json[1] + '", "db_type" : "' + new_json[0] + '" }')

            set_data = json.loads(open('data/set.json', encoding='utf8').read())

            break

def db_change(data):
    global set_data
    
    if set_data['db_type'] == 'mysql':
        data = data.replace('random()', 'rand()')
        data = data.replace('%', '%%')
        data = data.replace('?', '%s')

    return data

if set_data['db_type'] == 'mysql':
    try:
        set_data_mysql = json.loads(open('data/mysql.json', encoding='utf8').read())
    except:
        new_json = ['', '', '']

        while 1:
            print('DB user ID : ', end = '')
            new_json[0] = str(input())
            if new_json[0] != '':
                break

        while 1:
            print('DB password : ', end = '')
            new_json[1] = str(input())
            if new_json[1] != '':
                break
                
        print('DB host (localhost) : ', end = '')
        new_json[2] = str(input())
        if new_json[2] == '':
            new_json[2] == 'localhost'

        with open('data/mysql.json', 'w', encoding='utf8') as f:
            f.write('{ "user" : "' + new_json[0] + '", "password" : "' + new_json[1] + '", "host" : "' + new_json[2] + '" }')

        set_data_mysql = json.loads(open('data/mysql.json', encoding='utf8').read())

    conn = pymysql.connect(
        host = set_data_mysql['host'] if 'host' in set_data_mysql else 'localhost',
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

# Process
def editorProcess(editor):    
    return "N:" + editor if not re.search(r"^R:", editor) or not re.search(r'(\.|:)', editor) else editor

def url_pas(data):
    return urllib.parse.quote(data).replace('/','%2F')
    
def main_process(dictdata, get_num):
    editTime = str(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
    x = 0
    for d_dict in dictdata:        
        x += 1
        if x % 100 == 0:
            print(x)
            conn.commit()
        
        namespace = str(d_dict['namespace'])
        if namespace == '0' or namespace == '1':
            text = str(d_dict['text'])
            title = ('틀:' if namespace == '1' else '') + str(d_dict['title'])
                
            curs.execute(db_change("insert into data (title, data) values (?, ?)"), [title, text])
            
            if get_num == '1':
                revision = len(d_dict['contributors'])
                bulk_input = [[
                    str(y + 1), 
                    title, 
                    text if y == revision else '', 
                    editTime, 
                    editorProcess(d_dict['contributors'][y])
                ] for y in range(revision)]

                curs.executemany(db_change("insert into history (id, title, data, date, ip, send, leng, hide) values (?, ?, ?, ?, ?, '', '0', '')"), bulk_input)
            else:
                curs.execute(db_change("insert into history (id, title, data, date, ip, send, leng, hide) values ('1', ?, ?, ?, ?, ?, '0', '')"), [
                    title, 
                    text, 
                    editTime, 
                    'Tool:namujson'
                    'https://namu.wiki/history/' + url_pas(title)
                ])

    curs.execute(db_change('delete from other where name = "count_all_title"'))
    curs.execute(db_change('insert into other (name, data) values ("count_all_title", ?)'), [str(x)])

print('----')
print('1 : 전체 불러오기')
print('2 : data만 불러오기 (역사에는 나무위키 링크 삽입)')
print('모드 선택 : ', end = '')

get_num = input()
get_num = '1' if get_num == '1' else '2'

print('----')
print("이 스크립트는 나무위키 JSON 데이터가 필요합니다. 데이터를 로딩합니다.")

dictdata = json.load(open('namuwikidata.json', 'r', encoding = 'utf8'))

print("변환을 시작합니다.")
print('----')

main_process(dictdata, get_num)
conn.commit()

print('----')
print("문서 변환 작업이 종료되었습니다.")