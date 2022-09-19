"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import json
import os
import base64
import re
from pyfhirsdc.config import  get_defaut_path, get_fhir_cfg, get_processor_cfg,  read_config_file
from ..converters.utils import get_resource_url
from pyfhirsdc.serializers.http import post_multipart
from pyfhirsdc.serializers.json import  read_file, read_resource
from fhir.resources.relatedartifact import RelatedArtifact
from fhir.resources.library import Library
from fhir.resources.attachment import Attachment

def is_content_to_update(content, lib):
    return content.id.startswith("ig-loader-" + lib.id)

def refresh_content(lib):
    # for each lib check if there is the content "attachment.id = "ig-loader-" + id + ".cql""
    # replace  "ig-loader-" + id + ".cql" with the CQL file
    dependencies = []
    out_content = [x for x in lib.content if not is_content_to_update(x, lib)]
    if len (out_content) < len(lib.content):
        # get CQL file "ig-loader"
        cql = read_file(os.path.join(get_defaut_path('CQL', 'cql'), lib.id + '.cql') ,'str')
        out_content.append(get_cql_content(cql, lib.id))
        
        emls = update_eml_content(cql, lib.id)
        if emls is not None:
            for eml in emls:
                emlid = get_id_from_header(eml.headers[b'Content-Disposition'].decode())
                if emlid == lib.id:
                    out_content.append(get_eml_content(eml.text,emlid))# eml.content
                else:
                    dependencies.append(RelatedArtifact(
                        type = "depends-on",
                        resource = get_lib_url(emlid)
                    ))
                    
        return dependencies, out_content
                 
    return None, None

def get_lib_url(id):
    ext_libs = get_fhir_cfg().external_libraries
    if hasattr(ext_libs, id):
        return getattr(ext_libs,id)
    else:
        return get_resource_url("Library",id)


def get_id_from_header(header):
    match =   re.search('name="(?P<name>[\w.-]+)"',header)
    if 'name' in match.groupdict():
        return match.groupdict()['name']


def update_eml_content(cql, id):
    # get the depandencies
    # create the multipart payload
    # add dependencies recursivly
    multipart = {}
    build_multipart_cql(cql,id,multipart)
    print("sending cql {}".format(id))
    data = post_multipart(multipart, get_processor_cfg().cql_translator)
    if data is not None:
        return data.parts
    
    

def build_multipart_cql(cql,id,multipart): 
    multipart[id] = (id,cql,'application/cql')
    cql_deps = get_cql_dependencies(cql)
    for dep in cql_deps:

        if dep['id'] not in multipart:
            build_multipart_cql(dep['data'],dep['id'],multipart)

def get_cql_dependencies(cql):
    cqls = []
    pattern = "include ([0-0a-zA-Z-.]+)"
    matches = re.findall(pattern, cql, flags=0)
    for match in matches:
        cql = read_file(os.path.join(get_defaut_path('CQL', 'cql'), match + '.cql') ,'str')
        if cql is not None:
            cqls.append({'id':match, 'data':cql})
        else:
            print("Error, missing cql dependency "+match)
            exit()
            
    return cqls

def get_cql_content(cql,id):
    return Attachment(
        id = "ig-loader-" + str(id) + ".cql",
        contentType = "text/cql",
        data = base64.b64encode(cql.encode())
    )

def get_eml_content(cql,id):
    return Attachment(
        id = "ig-loader-" + str(id) + ".eml",
        contentType = "application/elm+json",
        data = base64.b64encode(cql.encode())
    )

def refresh_library(filepath):
    lib_json = read_resource(filepath, "Library")
    if lib_json is not None :
        lib = Library.parse_raw( json.dumps(lib_json))
        dependencies, content = refresh_content(lib)
        if content is not None and len(content)>0:
            lib.content = content
        if dependencies is not None and len(dependencies)>0:
            lib.relatedArtifact = dependencies
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

         