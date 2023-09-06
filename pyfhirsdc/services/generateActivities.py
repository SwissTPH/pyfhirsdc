"""
    Service to generate the activity ressources
    needs the sheet:
        - q.X
    Will be used in the plandefinition to call the respective questionnaires
"""
import logging

from pyfhirsdc.config import get_processor_cfg
from pyfhirsdc.converters.activityConverter import (create_activity_collect_with)
from pyfhirsdc.serializers.utils import (get_resource_path,
                                         get_resources_files, write_resource)

logger = logging.getLogger("default")

def generate_activities():
    questionnaires = get_resources_files('questionnaire')
    for questionnaire in questionnaires:
        generate_activity(questionnaire)

## generate questinnaire and questionnaire response
def generate_activity( questionnaire ) :
    # try to load the existing questionnaire
    fullpath = get_resource_path("ActivityDefinition", questionnaire["id"].lower())
    logger.info('processing activity {0}'.format(questionnaire["id"].lower()))
    # read file content if it exists
        # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    activity_definition = create_activity_collect_with(questionnaire)
    # write file
    write_resource(fullpath, activity_definition, get_processor_cfg().encoding)
