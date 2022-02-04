import os
from pathlib import Path
from pyfhirsdc.config import get_defaut_path, get_fhir_cfg, get_processor_cfg


def write_resource(filepath, resource, encoding):
    if not os.path.exists(Path(filepath).parent):
        os.makedirs(Path(filepath).parent)  
    try: 
        output = open(filepath, 'w', encoding='utf-8')
        output.write(resource.json(indent=4)) if encoding == "json" \
            else  output.write(resource.xml())
        output.close()
    except:
        raise ValueError("Error writing resource: "+ resource.id)

def get_resource_path(resource_type, name):
    if resource_type is not None and name is not None:
        path = get_defaut_path(resource_type, "resources/"+ resource_type.lower())
        if not os.path.exists(path):
            os.makedirs(path) 
        filename = resource_type.lower()+ "-"+ name +  "." + get_processor_cfg().encoding
        fullpath = os.path.join(path, filename)
        return fullpath

