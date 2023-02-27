
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace

from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.identifier import Identifier


def add_resource(path,name,bundle):
    file_path = os.path.join(path,name)
    ressource_dict = read_resource(file_path, 'any')
    if ressource_dict is not None and 'resourceType' in ressource_dict and 'url' in ressource_dict and ressource_dict['resourceType'] !='ImplementationGuide':
        
        bundle.entry.append(
            BundleEntry(
                fullUrl = ressource_dict['url'],
                request = BundleEntryRequest(
                    method  = 'PUT',
                    url =  ressource_dict['resourceType'] + '/' + ressource_dict['id']      
                ),
                resource= read_file(file_path, type = "str")
            )
        )

def write_resource(filepath, resource, encoding = None):
    if encoding is None:
        encoding = 'json'
    if not os.path.exists(Path(filepath).parent):
        os.makedirs(Path(filepath).parent)  
    try: 
        output = open(filepath, 'w', encoding='utf-8')
        if encoding == "json":
            output.write(resource.json(indent=4))
        elif encoding == "xml": 
            output.write(resource.xml()) 
        else:
            output.write(resource)
        output.close()
    except:
        if hasattr(resource, 'id'):
            raise ValueError("Error writing resource: "+ resource.id)
        else:
            raise ValueError("Error writing resource: "+ filepath)
        
def write_resource(filepath, resource, encoding = None):
    if encoding is None:
        encoding = "json"
    if not os.path.exists(Path(filepath).parent):
        os.makedirs(Path(filepath).parent)  
    try: 
        output = open(filepath, 'w', encoding='utf-8')
        if encoding == "json":
            output.write(resource.json(indent=4))
        elif encoding == "xml": 
            output.write(resource.xml()) 
        else:
            output.write(resource)
        output.close()
    except:
        if hasattr(resource, 'id'):
            raise ValueError("Error writing resource: "+ resource.id)
        else:
            raise ValueError("Error writing resource: "+ filepath)
        
def read_resource(filepath, resource):
    resource_dict = read_file(filepath, 'dict') if os.path.exists(filepath) else None

    # check if the resource has the right type 
    if resource_dict is not None and 'resourceType' in resource_dict\
        and (resource_dict['resourceType'] == resource  or resource == 'any'):
        return resource_dict
    else:
        return None


def read_file(filepath, type = "object"):
    json_str = None
    try:
        file = open(filepath, 'r',  encoding="utf-8")
        if type == "object":
            json_str = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
        elif type == "str":
            json_str = file.read()
        elif type == "dict":
            json_str = json.load(file)
            
        file.close()
    except IOError: 
        raise IOError("Error: File {0} does not appear to exist.".format(filepath))
    except ValueError as e:
        raise ValueError("file {0} failed to parse, please check the JSON structure".format(filepath))
    return json_str

def __main__():
    bundle = Bundle( identifier = Identifier(value = 'Bundle'),
                type  = 'batch', entry = [])
    # Read the config file

    folderdir = os.getcwd() 
    # giving file extensions
    ext = ('.json')
    # iterating over directory and subdirectory to get desired result
    for path, dirc, files in os.walk(folderdir):
        for name in files:
            if name.endswith(ext):
                logging.info('{}{}{}'.format( path, dirc , name)) # printing file name
                add_resource(path,name,bundle)
    write_resource('./bundle.json', bundle)