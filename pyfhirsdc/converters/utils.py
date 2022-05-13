import os
from pathlib import Path
from pyfhirsdc.config import  get_fhir_cfg,  get_processor_cfg


def get_resource_name(resource_type, name):
    return resource_type.lower()+ "-"+ clean_name(name)

def get_resource_url(resource_type, id):
    return str(get_fhir_cfg().canonicalBase +  resource_type + "/" + clean_name(id))

def clean_name(name):
    return str(name.replace(" ","-").replace("_","-").replace("-+","-").lower())

def get_custom_codesystem_url():
    return get_resource_url (
            'CodeSystem', 
            get_processor_cfg().scope+"-custom-codes"
            )