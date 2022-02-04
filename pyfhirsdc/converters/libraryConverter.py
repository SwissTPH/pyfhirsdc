import os
import pandas as pd
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg
from pyfhirsdc.utils import write_resource
from pyfhirsdc.converters.planDefinitionConverter import getIdentifierFirstRep,  write_action_condition, getActionFirstRep
from fhir.resources.library import Library
from fhir.resources.attachment import Attachment
from fhir.resources.fhirtypes import Canonical

### Function that creates the constant part of cql files 
def writeLibraryHeader(library,scope):
    return "library "+ library.name + "\n\n "+"using FHIR version" + library.version + "\n\n "+ "include FHIRHelpers version '{0}'".format(library.version)+ "\n\n "+ \
        "include " + scope + "Concepts called Config" + "\n "+ "include " + scope + "Concepts called Cx" + "\n " + "include "+scope+"DataElements called PatientData"+ "\n\n "+\
            "context Patient"+ "\n\n " 


def write_libraries(output_path,libraries, encoding):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if libraries is not None and len(libraries)>0:
        for library in libraries.items():
            write_resource(output_path,library, encoding)
  
def write_library_CQL(output_path, name, cql):
    if cql is not None and len(cql)>0:
        output_file_path = os.path.join(output_path, name + ".cql")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        for entry in cql:    
            output.write(cql[entry])

def generate_plan_defnition_lib(planDefinition):
    id = planDefinition.id
    library = Library.construct()
    library.status = get_fhir_cfg().Library.status
    ## The fhir classes are being initialized with value None so, if it is None we create a list
    if not library.identifier: library.identifier = []
    library.identifier.append(getIdentifierFirstRep(planDefinition))
    library.id = id
    library.name = planDefinition.name
    print("Generating library ", library.name, ".......")
    library.version = " " + get_fhir_cfg().version
    library.url = get_fhir_cfg().canonicalBase + '/Library/' + id 
    library.title = planDefinition.title
    library.description = planDefinition.description
    attachment = Attachment.construct()
    attachment.id = "ig-loader-" + id + ".cql"
    library.content = [attachment]
    libraryCanonical = Canonical(library.url)
    if not planDefinition.library:  planDefinition.library = []    
    planDefinition.library.append(libraryCanonical)
    cql = {}
    cql['header'] = writeLibraryHeader(library, get_processor_cfg().scope)
    i = 0
    list_actions = getActionFirstRep(planDefinition).action
    if list_actions:
        for action in list_actions:
            if (action.condition):
                
                action_cql = write_action_condition(action)
                if action_cql is not None:
                    cql[i] = action_cql
                    i = i+1
    
    return cql, library