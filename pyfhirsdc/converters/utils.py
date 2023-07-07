import logging
from datetime import datetime, timezone
import validators

import pandas as pd
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

from pyfhirsdc.config import get_dict_df, get_fhir_cfg, get_processor_cfg

logger = logging.getLogger("default")

def get_resource_name(resource_type, name):
    return resource_type.lower()+ "-"+ clean_name(name)

def get_resource_url(resource_type, id):
    return str(get_fhir_cfg().canonicalBase +  resource_type + "/" + clean_name(id))

def clean_name(name, lower = True):
    ret = str(name).replace(" ","-").replace("_","-").replace("-+","-")
    return ret.lower() if lower else ret

def clean_group_name(name):
    return clean_name(name).replace('-','').replace('.','').replace('/','').replace('&','').strip()

def get_custom_codesystem_url():
    return get_resource_url (
            'CodeSystem', 
            get_processor_cfg().scope+"-custom-codes"
            )
    
    
def inject_sub_questionnaires(df_questions):
    for s_id, s_row in df_questions[df_questions.type == "questionnaire"].iterrows():
        df_questions = inject_sub_questionnaire(df_questions, s_row['id'])
    return df_questions



def inject_sub_questionnaire(df_questions, questionnaire_name):

    # find the questionnaire
    dict_questionnaire_df = get_dict_df()['questionnaires']
    if questionnaire_name in dict_questionnaire_df:
        sub_questionnaire = dict_questionnaire_df[questionnaire_name].copy()
        load_sub_questionnaire = sub_questionnaire[pd.notna(sub_questionnaire.initialExpression) | (sub_questionnaire.id=="{{library}}")]
        sub_questionnaire=sub_questionnaire[pd.isna(sub_questionnaire.initialExpression) & (sub_questionnaire.id!="{{library}}")]
        
        
        if 'parentId' in sub_questionnaire:
            mask = pd.isna(sub_questionnaire['parentId'])
            sub_questionnaire.loc[mask, 'parentId'] = questionnaire_name
            
            
            
#            updated_parentid = []
#            for id, row in sub_questionnaire.iterrows():
#                updated_parentid.append( row['parentId'] if pd.notna(row['parentId']) else questionnaire_name)
#            sub_questionnaire.update(pd.DataFrame({'parentId':updated_parentid}))
            
            
        else:
            sub_questionnaire['parentId'] = [questionnaire_name  for x in range(len(sub_questionnaire))]
        df_questions = pd.concat([df_questions,sub_questionnaire], ignore_index=True)
        # inject the load 
        for s_id, s_row in load_sub_questionnaire.iterrows(): 
            if len(df_questions[df_questions.id == s_row['id']])==0:
                df_questions.loc[len(df_questions.index)]=s_row
                #df_questions.append(s_row)
    # inject the questionnaire questions as child quesiton
    return df_questions
    
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
    
FHIR_BASE_PROFILES = [
    "Patient",
    "RelatedPerson",
    "Encounter",
    "Condition",
    "Observation",
    "QuestionnaireResponse",
    "CommunicationRequest"
]

def get_base_profile(profile):
    for base_profile in FHIR_BASE_PROFILES:
        if base_profile.lower() in profile.lower():
            return base_profile
        
def get_media(question):
    display_str = str(question["media"]) if "media" in question and pd.notna(question["media"]) else None
    if display_str is not None:
        arr =  display_str.split('::')
        if len(arr)==2:
            url = arr[1].replace('{{canonical_base}}',get_fhir_cfg().canonicalBase)
            is_url = validators.url(url)
            if not is_url:
                url = get_fhir_cfg().canonicalBase + "Binary/" +arr[1]
            return arr[0], url
        else:
            logger.error("Media must have 2 parameters type, url")
    return None, None
    
def get_fpath(df_questions, linkid, fpath = [] ):
    # get the questions
    question = df_questions[(df_questions['id'] == linkid) | (df_questions['label'] == linkid) ]
    if len(question) == 0:
        # look but with the
        question = df_questions[df_questions['id'] == linkid]
        logger.error(" {} not found in id or label".format(linkid))
        exit()
    elif len(question) > 1:
        # look but with the
        question = df_questions[df_questions['id'] == linkid]
        logger.error(" {}  found several times in id or label ".format(linkid))
        exit()
    #find if there is parent
    question = question.iloc[0]
    fpath.append(question['id'])
    
    if "parentId" in question and pd.notna(question.parentId) :
        if question.parentId not in fpath:
            return get_fpath(df_questions, question.parentId, fpath)
        else:
            logger.error("loop detected involving {} and {} ".format(linkid, question.parentId))
            exit()
    else:
        return fpath
    # if yes recursive call until no parent or loop
    
def inject_config(value):
    return value.replace('{{cs_url}}',  get_custom_codesystem_url()).replace('{{canonical_base}}',  get_fhir_cfg().canonicalBase)