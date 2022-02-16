import os
from pathlib import Path
from pyfhirsdc.config import  get_fhir_cfg,  get_processor_cfg


def get_resource_name(resource_type, name):
    return resource_type.lower()+ "-"+ name 

def get_resource_url(resource_type, name):
    return get_fhir_cfg().canonicalBase +  get_resource_name(resource_type, name)

def clean_name(name):
    return name.replace(" ","-").replace("_","-").lower()

def get_custom_codesystem_url():
    return get_resource_url (
            'CodeSystem', 
            get_processor_cfg().scope+"-custom-codes"
            ) 