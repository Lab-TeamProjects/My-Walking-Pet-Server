import json
from json.decoder import JSONDecoder
from os import error
import requests

def Send():
    #headers = { 'content-type': 'application/json' }
    
    # = """[ "variables": {"id": "12345", "input": {"Id": "111", "type": "test", "item": "0", "Id2": "null", "page": "1", "display":10, "info": true }}}]"""

    # response = requests.post("http://203.232.193.164:9999/sign-up", json={"email" : "ging1030l@gmail.com", "password" : "1234"})
    
    response = requests.post("http://localhost:9999/login", json={"email" : "ging1030l@gmail.com", "password" : "1234"})
    
    return response.text

Send()
Send()

