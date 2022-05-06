import os
import pandas as pd
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.utils import get_resource_url
from pyfhirsdc.serializers.utils import write_resource
from pyfhirsdc.converters.planDefinitionConverter import getIdentifierFirstRep,  write_action_condition
from fhir.resources.library import Library
from fhir.resources.attachment import Attachment
from fhir.resources.fhirtypes import Canonical
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
### Function that creates the constant part of cql files 
def writeLibraryHeader(library,scope):
    return "library "+ library.name + "\n\n "+"using FHIR version" + library.version + "\n\n "+ "include FHIRHelpers version '{0}'".format(library.version)+ "\n\n "+ \
        "include " + scope + "Concepts called Config" + "\n "+ "include " + scope + "Concepts called Cx" + "\n " + "include "+scope+"DataElements called PatientData"+ "\n\n "+\
            "context Patient"+ "\n\n " 

  
def write_library_CQL(output_path, lib, cql):
    if cql is not None and len(cql)>0:
        output_file_path = os.path.join(output_path, lib.name + ".cql")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        for entry in cql:    
            output.write(cql[entry])

def generate_plan_defnition_lib(planDefinition):
    id = planDefinition.id
    print("Generating library ", planDefinition.name, ".......")
    library = Library(
        id = id,
        identifier = [getIdentifierFirstRep(planDefinition)],
        status = get_fhir_cfg().Library.status,
        name = planDefinition.name,
        version = " " + get_fhir_cfg().version,
        title = planDefinition.title,
        description = planDefinition.description,
        url = get_resource_url('Library', id),
        content = [Attachment(
            id = "ig-loader-" + id + ".cql"
        )],
        type = CodeableConcept(
            coding= [Coding(                
                system = "http://hl7.org/fhir/ValueSet/library-type",
                code = 'logic-library'
                )]
        )
    )
    libraryCanonical = Canonical(library.url)
    if not planDefinition.library:  planDefinition.library = []    
    planDefinition.library.append(libraryCanonical)
    cql = {}
    cql['header'] = writeLibraryHeader(library, get_processor_cfg().scope)
    i = 0
    list_actions = planDefinition.action
    if list_actions:
        for action in list_actions:
            if (action and action.condition):       
                action_cql = write_action_condition(action)
                if action_cql is not None:
                    cql[i] = action_cql
                    i = i+1
    
    return cql, library