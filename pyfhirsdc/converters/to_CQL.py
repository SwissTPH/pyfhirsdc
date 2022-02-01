import os
import pandas as pd
from ..utils import getConditionFirstRep, getIdentifierFirstRep, getActionFirstRep
from fhir.resources.attachment import Attachment
from fhir.resources.fhirtypes import Canonical
from fhir.resources.library import Library

### Function that creates the constant part of cql files 
def writeLibraryHeader(library,scope):
    return "library "+ library.name + "\n\n "+"using FHIR version" + library.version + "\n\n "+ "include FHIRHelpers version '{0}'".format(library.version)+ "\n\n "+ \
        "include " + scope + "Concepts called Config" + "\n "+ "include " + scope + "Concepts called Cx" + "\n " + "include "+scope+"DataElements called PatientData"+ "\n\n "+\
            "context Patient"+ "\n\n " 


def write_action_condition(cql, action):
    condition = getConditionFirstRep(action)
    if (not pd.isnull(condition.expression.expression)):
        condition.expression.expression = "Should {0}".format(action.description.replace("\"", "\\\"") \
            if action.description else "perform action")
    
    ## Output false, manual process to convert the pseudo-code to CQL
    cql+= "/*\n "+getConditionFirstRep(action).expression.description+"\n */\n "+\
        "define \"{0}\":\n ".format(getConditionFirstRep(action).expression.expression)+ \
            "  false" + "\n\n "

def write_plan_definitions(plandefinitions,encoding,outputpath):
    if pd.notnull(plandefinitions) and len(plandefinitions)>0:
        for key, value in plandefinitions.items():
            output_path_file = os.path.join(outputpath,"input","resources","plandefinition")
            if (os.path.exists):
                write_resource(output_path_file, value, encoding)
            else:
                raise ValueError("The validity of the path could not be established")

def write_resource(output_file, resource, encoding):
    if not os.path.exists(output_file):
            os.makedirs(output_file)
    output_file_path = os.path.join(output_file,resource.resource_type.lower()+\
        "-" + resource.id + "." + encoding)
    try: 
        output = open(output_file_path, 'w', encoding='utf-8')
        output.write(resource.json()) if encoding == "json" \
            else  output.write(resource.xml())
        output.close()
    except:
        raise ValueError("Error writing resource: "+ resource.id)

def build_plan_definition_index(planDefinitions):
    index =  "### Plan Definitions by Decision ID\n\n "+\
    "|Decision Table|Description| \n "+"|---|---|\n "
    for key, plan_definition in planDefinitions.items():
        index += "|[{0}](PlanDefinition-{1}.html)|{2}|".format(\
            plan_definition.title, plan_definition.id, 
            plan_definition.description)
        index += "\n "
    return index

def write_library_CQL(output_path, libraryCQL):
    if (pd.notnull(libraryCQL) and len(libraryCQL) >0):
        for entry in libraryCQL:
            output_directory_path = os.path.join(\
                output_path, "input", "cql")
            output_file_path = os.path.join(output_directory_path,
            entry + ".cql")
        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        output.write(libraryCQL[entry])

def write_plan_definition_index(planDefinitions, output_path):
    output_file_path = os.path.join(output_path, 
    "pagecontent") 
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)
    else:
        output = open(output_file_path+"PlanDefinitionIndex.md", 'w')
        output.write(build_plan_definition_index(planDefinitions))

def write_libraries(output_path,libraries, encoding):
    output_file_path = os.path.join(output_path, 
    "input", "resources", "library") 
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)
    if pd.notnull(libraries) and len(libraries)>0:
        for key, library in libraries.items():
            write_resource(output_file_path,library, encoding)
  
def generateLibrary(planDefinition, canonicalBase, libraryStatus,libraryVersion,scope,libraries,libraryCQL):
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