import os
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
        output.write(resource.json(indent=4)) if encoding == "json" \
            else  output.write(resource.xml())
        output.close()
    except:
        raise ValueError("Error writing resource: "+ resource.id)

def get_resource_path(resource_type, name, encoding = None):
    if encoding is None:
        encoding = get_processor_cfg().encoding
    if resource_type is not None and name is not None:
        path = get_defaut_path(resource_type, "resources/"+ resource_type.lower())
        if not os.path.exists(path):
            os.makedirs(path) 
        filename = get_resource_name(resource_type, name)+  "." + encoding
        fullpath = os.path.join(path, filename)
        return fullpath