import os
import pandas as pd
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
    if pd.notnull(libraries) and len(libraries)>0:
        for key, library in libraries.items():
            write_resource(output_path,library, encoding)
  
def write_library_CQL(output_path, libraryCQL):
    if (pd.notnull(libraryCQL) and len(libraryCQL) >0):
        for entry in libraryCQL:
            output_file_path = os.path.join(output_path,
            entry + ".cql")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        output.write(libraryCQL[entry])

def generate_plan_defnition_lib(planDefinition, canonicalBase, libraryStatus,libraryVersion,scope,libraries,libraryCQL):
  id = planDefinition.id
  library = Library.construct()
  library.status = libraryStatus
  ## The fhir classes are being initialized with value None so, if it is None we create a list
  if not library.identifier: library.identifier = []
  library.identifier.append(getIdentifierFirstRep(planDefinition))
  library.id = id
  library.name = planDefinition.name
  print("Generating library ", library.name, ".......")
  library.version=libraryVersion
  library.url = canonicalBase + '/Library/' + id 
  library.title = planDefinition.title
  library.description = planDefinition.description
  attachment = Attachment.construct()
  attachment.id = "ig-loader-" + id + ".cql"
  library.content = [attachment]
  libraryCanonical = Canonical(library.url)
  if not planDefinition.library:  planDefinition.library = []    
  planDefinition.library.append(libraryCanonical)
  print(planDefinition.library)
  print("library: ", library.version)
  cql = writeLibraryHeader(library,scope)
  list_actions =getActionFirstRep(planDefinition).action
  if list_actions:
      for action in list_actions:
          if (action.condition):
              write_action_condition(cql, action)
  libraries[id]= library
  libraryCQL[id] = cql
  return libraryCQL, libraries