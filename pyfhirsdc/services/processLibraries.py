"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import base64
import json
import logging
import os
import re

from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.library import Library
from fhir.resources.R4B.relatedartifact import RelatedArtifact

from pyfhirsdc.config import (get_defaut_path, get_fhir_cfg, get_processor_cfg,
                              read_config_file)
from pyfhirsdc.serializers.http import check_internet, post_multipart
from pyfhirsdc.serializers.json import read_file, read_resource
from pyfhirsdc.version import __version__
from ..converters.utils import get_custom_codesystem_url, get_resource_url

logger = logging.getLogger("default")
def is_content_to_update(content, lib):
    return content.id.startswith("ig-loader-" + lib.name)

def refresh_content(lib):
    # for each lib check if there is the content "attachment.id = "ig-loader-" + id + ".cql""
    # replace  "ig-loader-" + id + ".cql" with the CQL file
    dependencies = []
    out_content = [x for x in lib.content if not is_content_to_update(x, lib)]
    if len (out_content) < len(lib.content):
        # get CQL file "ig-loader"
        cql = read_file(os.path.join(get_defaut_path('CQL', 'cql'), lib.name + '.cql') ,'str')
        out_content.append(get_cql_content(cql, lib.name))
        deps = get_cql_dependencies(cql,[])
        if get_processor_cfg().generateElm == True and check_internet(): # create the elm
            multipart = build_multipart_cql(cql,lib.name, deps, {})
            emls = update_eml_content(multipart, lib.name, 'json')
            if emls is not None and get_processor_cfg().saveElm == True:
                for eml in emls:
                    emlid = get_id_from_header(eml.headers[b'Content-Disposition'].decode())
                    if emlid == lib.name:
                        out_content.append(get_eml_content(eml.text,emlid,'json'))# eml.content
                        #elms_xml = update_eml_content(multipart, lib.id, 'json')
                        #for elm_xml in elms_xml:
                        #    emlid = get_id_from_header(elm_xml.headers[b'Content-Disposition'].decode())
                        #    if emlid == lib.id:
                        #        out_content.append(get_eml_content(eml.text,emlid,'xml'))

        for dep in deps:
            dependencies.append(RelatedArtifact(
                        type = "depends-on",
                        resource = get_lib_url(dep['name'])
                    ))

        return dependencies if len(dependencies)>0 else None, out_content    
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



def update_eml_content(multipart, id, ext):
    
    from jsonpath_ng import jsonpath, parse

    # get the depandencies
    # create the multipart payload
    # add dependencies recursivly
    logger.info("sending cql {}".format(id))
    data = post_multipart(multipart, get_processor_cfg().cql_translator+('&' if '?' in get_processor_cfg().cql_translator else '?') +"format="+ext)
    if data is not None:
        
        for elm in data.parts:
            error_str = '"errorSeverity" : "error"'
            json_w_error = None
            match = None
            if error_str in elm.text:
                logger.error(" found in "+id)
                json_w_error = json.loads(elm.text)
                jsonpath_expression = parse('$.library.annotation[*]')
                match = jsonpath_expression.find(json_w_error)
                for val in match:
                    logger.error(val.value)
                    
                match.clear()
                data.parts = ()
                return None
        return data.parts

    
    

def build_multipart_cql(cql,name, cql_deps,multipart = {}):
    if id not in multipart:
        multipart[name] = (name,cql,'application/cql')
        for dep in cql_deps:
            if dep['name'] not in multipart:
                multipart[dep['name']] = (dep['name'],dep['data'],'application/cql')
               
    return multipart

def get_cql_dependencies(cql, cqls = []):
    pattern = "include ([0-9a-zA-Z\-\.]+)(?:\n| )"
    matches = re.findall(pattern, cql, flags=0)
    for match in matches:
        if match not in get_cqls_ids(cqls):
            file_path = os.path.join(get_defaut_path('CQL', 'cql'), match + '.cql')
            if os.path.exists(file_path):
                sub_cql = read_file(file_path ,'str')
                if sub_cql is not None:
                    cqls.append({'name':match, 'data':sub_cql})
                    cqls = get_cql_dependencies(sub_cql, cqls)
                else:
                    logger.error(" missing cql dependency "+match)
                    exit()
            else:
                logger.error(" missing cql dependency "+match)
                exit()
                
    return cqls

def get_cqls_ids(cqls):
    return [x['name'] for x in cqls]

def get_cql_content(cql,name):
    return Attachment(
        id = "ig-loader-" + str(name) + ".cql",
        contentType = "text/cql",
        data = base64.b64encode(cql.encode())
    )

def get_eml_content(cql,name, ext = 'json'):
    return Attachment(
        id = "ig-loader-" + str(name) + ".eml",
        contentType = "application/elm+"+ext,
        data = base64.b64encode(cql.encode())
    )

def refresh_library(filepath):
    lib_json = read_resource(filepath, "Library")
    if lib_json is not None :
        lib = Library.parse_raw( json.dumps(lib_json))
        #FIXME
        dependencies, content = refresh_content(lib)
        if content is not None and len(content)>0:
            lib.content = content
        if dependencies is not None and len(dependencies)>0:
            lib.relatedArtifact = dependencies
        # write file
        
        with open(filepath, 'w') as json_file:
            json_file.write(lib.json( indent=4))

def add_manual_content(manual_lib_path,lib_path, cql_lib_path, cql_path ):
    if os.path.exists(manual_lib_path) and os.path.exists(cql_lib_path):

        arr_lib_file_path = os.listdir(manual_lib_path)
        for file in arr_lib_file_path:
            if file.endswith(".json") :
                update_lib_version(
                    os.path.join(manual_lib_path, file),
                    os.path.join(lib_path, file)
                )
        arr_lib_file_path = os.listdir(cql_lib_path)
        for file in arr_lib_file_path:
            if file.endswith(".json") or file.endswith(".cql"):
                update_lib_version(
                    os.path.join(cql_lib_path, file),
                    os.path.join(cql_path, file)
                )          

def process_libraries(conf):
    # Read the config file
    config_obj = read_config_file(conf)

    if config_obj is None:
        exit()
    else:
    # copy the manual libs
    #TODO dynamic path
        core_cql =  os.path.join(os.path.dirname(__file__),  "../core_fhir/cql")
        core_lib =  os.path.join(os.path.dirname(__file__),  "../core_fhir/resources/library")
    
        lib_path = get_defaut_path('Library', 'ressources/library')
        cql_path = get_defaut_path('CQL', 'cql')
        manual_lib_path = os.path.join(get_processor_cfg().manual_content,"resources/library")
        cql_lib_path = os.path.join(get_processor_cfg().manual_content,"cql")
        add_manual_content(core_lib,lib_path, core_cql, cql_path )
        add_manual_content(manual_lib_path,lib_path, cql_lib_path, cql_path )
        
        arr_lib_file_path = os.listdir(lib_path)
        for file in arr_lib_file_path:
            if file.endswith(".json"):
               refresh_library(os.path.join(lib_path,file)) 
        # get libraries 

def update_lib_version(src,dst):
    
    with open(src, 'r') as file :
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace("{{LIB_VERSION}}",get_fhir_cfg().lib_version)\
        .replace("{{cs_url}}",get_custom_codesystem_url())\
        .replace("{{FHIR_VERSION}}",get_fhir_cfg().version)\
        .replace("{{canonical_base}}",get_fhir_cfg().canonicalBase)\
        .replace("{{pyfhirsdc_version}}",__version__)
    

    # Write the file out 
    with open(dst, 'w') as file:
        file.write(filedata)         
        