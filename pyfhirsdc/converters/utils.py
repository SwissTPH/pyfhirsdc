from datetime import datetime, timezone

import pandas as pd
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg


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
    
def get_breadcrumb(df_questions, linkid, breadcrumb = [] ):
    # get the questions
    question = df_questions[(df_questions['id'] == linkid) | (df_questions['label'] == linkid) ]
    if len(question) == 0:
        # look but with the
        question = df_questions[df_questions['id'] == linkid]
        print("error: {} not found in id or label".format(linkid))
        exit()
    elif len(question) > 1:
        # look but with the
        question = df_questions[df_questions['id'] == linkid]
        print("error: {}  found several times in id or label ".format(linkid))
        exit()
    #find if there is parent
    question = question.iloc[0]
    breadcrumb.append(question['id'])
    
    if "parentId" in question and pd.notna(question.parentId) :
        if question.parentId not in breadcrumb:
            return get_breadcrumb(df_questions, question.parentId, breadcrumb)
        else:
            print("error: loop detected involving {} and {} ".format(linkid, question.parentId))
            exit()
    else:
        return breadcrumb
    # if yes recursive call until no parent or loop