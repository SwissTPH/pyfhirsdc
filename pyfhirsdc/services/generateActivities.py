"""
    Service to generate the activity ressources
    needs the sheet:
        - q.X
    Will be used in the plandefinition to call the respective questionnaires
"""

from pyfhirsdc.converters.structureMapConverter import add_structure_maps_url, get_structure_map_bundle
from pyfhirsdc.config import  get_processor_cfg
from pyfhirsdc.converters.activityConverter import init_activity, create_activity
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource, get_resources_files
import numpy as np

def generate_activities():
    questionnaires = get_resources_files('questionnaire')
    for questionnaire in questionnaires:
        generate_activity(questionnaire)

## generate questinnaire and questionnaire response
def generate_activity( questionnaire ) :
    # try to load the existing questionnaire
    fullpath = get_resource_path("ActivityDefinition", questionnaire["id"].lower())
    print('processing activity {0}'.format(questionnaire["id"].lower()))
    # read file content if it exists
    activity_definition = init_activity(fullpath, questionnaire["id"].lower())
        # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    activity_definition = create_activity(activity_definition,questionnaire)
    # write file
    write_resource(fullpath, activity_definition, get_processor_cfg().encoding)
