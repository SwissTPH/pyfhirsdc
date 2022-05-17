import requests
import json
from pyfhirsdc.serializers.json import read_json

def put_files(file_path, url):
    print("Sending the file {0}".format(url))
    buffer= read_json(file_path, type = "str")
    headers_map = {'Content-type': 'application/json'}
    response = requests.put(url, data = buffer.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        print(response.status_code)
    else:
        print(str(response.status_code))
        print(response.text)