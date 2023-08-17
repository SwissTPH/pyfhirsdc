import json
import os
import sys 

from pathlib import Path


from pyfhirsdc.config import get_defaut_path, get_processor_cfg
from pyfhirsdc.converters.utils import get_resource_name


def write_resource(filepath, resource, encoding = None):
    if encoding is None:
        encoding = get_processor_cfg().encoding
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

def get_resource_path(resource_type, name, encoding = None, generateName = True ):
    if encoding is None:
        encoding = get_processor_cfg().encoding
    if resource_type is not None and name is not None:
        path = get_defaut_path(resource_type, "resources/"+ resource_type.lower())
        if not os.path.exists(path):
            os.makedirs(path) 
        if generateName:
            filename = get_resource_name(resource_type, name)+  "." + encoding
        else:
            filename =  name + "." + encoding
        fullpath = os.path.join(path, filename)
        return fullpath

def get_page_content_path(path, fileName, encoding = None):
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if path is not None and fileName is not None:
        path = get_defaut_path(fileName, "pagecontent/" + fileName.lower())
    fullpath = os.path.join(path)
    return fullpath

def write_page_content(filePath, pagetitle, content, encoding=None):
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if not os.path.exists(Path(filePath).parent):
        os.mkdirs(Path(filePath).parent)

    try: 
        output = open(filePath, 'w', encoding=encoding)
        output.write("# " + pagetitle + "\n\n")
        output.write(content)
        output.close()
    except: 
        raise ValueError("Error writing page content: " + filePath)

def get_resources_files(resource_type):
    path = get_defaut_path(resource_type, "resources/"+ resource_type.lower())
    resources = []
    for p in Path(path).glob('*.json'):
        json_obj = json.loads(p.read_text())
        resources.append(json_obj)
    return resources

def reindent(s, numSpaces):
    arr = [y for y in (x.rstrip() for x in s.splitlines()) if y]
    arr = [(numSpaces * ' ') + line for line in arr]
    return "\n".join(arr)

