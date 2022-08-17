"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import json
import os
import base64
from pyfhirsdc.config import  get_defaut_path,  read_config_file
from pyfhirsdc.serializers.json import  read_resource

from fhir.resources.library import Library
from fhir.resources.attachment import Attachment

def is_content_to_update(content, lib):
    return content.id == "ig-loader-" + lib.id + ".cql"

def refresh_content(lib):
    # for each lib check if there is the content "attachment.id = "ig-loader-" + id + ".cql""
    # replace  "ig-loader-" + id + ".cql" with the CQL file
    out_content = [x for x in lib.content if not is_content_to_update(x, lib)]
    if len (out_content) + 1  == len(lib.content):
        # get CQL file
        cql_path = get_defaut_path('CQL', 'cql')
        file_path = os.path.join(cql_path, lib.id + '.cql')
        if os.path.exists(file_path):
            f = open(file_path, "rb")
            cql_content = f.read()
            content = Attachment(
                id = "ig-loader-" + str(lib.id) + ".cql",
                contentType = "text/cql",
                data = base64.b64encode(cql_content)
            )
            if content is not None:
                out_content.append(content)
                return out_content
                 
    return None


def refresh_library(filepath):
    lib_json = read_resource(filepath, "Library")
    if lib_json is not None :
        lib = Library.parse_raw( json.dumps(lib_json))
        content = refresh_content(lib)
        if content is not None:
            lib.content = content
        # write file
            with open(filepath, 'w') as json_file:
                json_file.write(lib.json( indent=4))

def process_libraries(conf):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        lib_path = get_defaut_path('Library', '/ressources/library')
        arr_lib_file_path = os.listdir(lib_path)
        for file in arr_lib_file_path:
            if file.endswith(".json"):
               refresh_library(os.path.join(lib_path,file)) 
        # get libraries 

         