from datetime import datetime
from datetime import timezone
import os
from pathlib import Path
from pyfhirsdc.config import  get_fhir_cfg,  get_processor_cfg
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

def get_resource_name(resource_type, name):
    return resource_type.lower()+ "-"+ clean_name(name)

def get_resource_url(resource_type, id):
    return str(get_fhir_cfg().canonicalBase +  resource_type + "/" + clean_name(id))

def clean_name(name, lower = True):
    ret = str(name).replace(" ","-").replace("_","-").replace("-+","-")
    return ret.lower() if lower else ret

def clean_group_name(name):
    return clean_name(name).replace('-','').replace('.','').replace('/','').strip()

def get_custom_codesystem_url():
    return get_resource_url (
            'CodeSystem', 
            get_processor_cfg().scope+"-custom-codes"
            )
    
def init_resource_meta(resource):
    resource.date = datetime.now(timezone.utc).isoformat('T', 'seconds')
    resource.experimental = False
    resource.status = "active"

def init_list(list):
    if list is None:
        list = []
    
def get_codableconcept_code(system, code, display = None):
    return CodeableConcept(
            coding= [get_code(system, code, display)]
    )
def get_code(system, code, display = None ):
    return Coding(                
                system = system,
                code = code,
                display = display
                )
    