import requests
import json
from pyfhirsdc.serializers.json import read_file
from requests_toolbelt.multipart import decoder

def put_files(file_path, url):
    print("Sending the file {0}".format(url))
    buffer= read_file(file_path, type = "str")
    headers_map = {'Content-type': 'application/json'}
    response = requests.put(url, data = buffer.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        print(response.status_code)
    else:
        print(str(response.status_code))
        print(response.text)
        
def post_files(file_path, url):
    print("Sending the file {0}".format(url))
    buffer= read_file(file_path, type = "str")
    headers_map = {'Content-type': 'application/json'}
    response = requests.post(url, data = buffer.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        print(response.status_code)
    else:
        print(str(response.status_code))
        print(response.text)

def post_multipart(list, url):
    print("Sending the multipart to {0} and pasing multipart answer".format(url))
    response = requests.post(url, files = list,headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200 or response.status_code == 201 :
        print(response.status_code)
        multipart_data = decoder.MultipartDecoder.from_response(response)
        return multipart_data
    else:
        print(str(response.status_code))
        print(response.text)            