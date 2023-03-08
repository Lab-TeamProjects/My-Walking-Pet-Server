import json
from json.decoder import JSONDecoder
from os import error
import requests

server = 'http://203.232.193.164:5000'

def Sign_up():
    #headers = { 'content-type': 'application/json' }
    
    # = """[ "variables": {"id": "12345", "input": {"Id": "111", "type": "test", "item": "0", "Id2": "null", "page": "1", "display":10, "info": true }}}]"""

    # response = requests.post("http://203.232.193.164:9999/sign-up", json={"email" : "ging1030l@gmail.com", "password" : "1234"})
    
    url = "http://localhost:5000/sign-up"
    
    data = {"email" : "ging1030l@gmail.com", "password" : "1234"}
    access_token = 'my_access_token'
    headers = {'Authrization': f'Bearer {access_token}'}

    json_data = json.dumps(data)
    headers.update({'Content-Type': 'application/json'})

    response = requests.post(url, headers=headers, data=json_data)
    
    return response.json()


def Login():
    url = server + "/login"
    
    data = {"email" : "ging1030l@gmail.com", "password" : "1234"}
    access_token = 'my_access_token'
    headers = {'Authrization': f'Bearer {access_token}'}

    json_data = json.dumps(data)
    headers.update({'Content-Type': 'application/json'})

    response = requests.post(url, headers=headers, data=json_data)
    
    return response.json()

def login_test(access_token):
    url = server + "/login-test"
    
    headers = {'Authorization': f'Bearer {access_token}'}

    headers.update({'Content-Type': 'application/json'})

    response = requests.get(url, headers=headers)
    
    return response.json()

login = Login()
access_token = login['access_token']
print(access_token)
print('토큰 발급 완료')
result = login_test(access_token)

print(result)

