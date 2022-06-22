import requests
import json
from pyfhirsdc.serializers.json import read_json
import re 
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

def post_cql(cql_merged, url):
    print("Sending the cql to be translated at {0}".format(url))
    headers_map = {'Content-type': 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW',
                    'Accept': 'multipart/form-data'
    }
    response = requests.post(url, data = cql_merged.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        ##print(response.text[:45])
        json_strings = re.findall(r'.*({\\\"library\\.*})',response.text)
        json_library_array = []
        for json_string in json_strings:
            print(json_string)
            json_data = json.loads(json_string)
            json_library_array.append(json_data)
        print(response.text[:45])
        print(json_library_array)
        return json_library_array
    else:
        print(str(response.status_code))
        print(response.text)
