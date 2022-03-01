"""
    Service to generate the Structure definition (profiles)
    needs the sheet:
        - profiles
        - q.X
"""

from tkinter.font import names
from pyfhirsdc.converters.structureMapConverter import add_structure_maps_url, get_structure_maps
from pyfhirsdc.config import  get_processor_cfg
from pyfhirsdc.converters.questionnaireItemConverter import convert_df_to_questionitems, init_questionnaire
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource
from pyfhirsdc.converters.profileConverter import convert_df_to_extension_profiles
from pyfhirsdc.converters.profileConverter import convert_df_to_profiles
import pandas as pd 


def generate_profiles(dfs_questionnaire, df_profile):
    for name, questions in dfs_questionnaire.items():
        if not questions["id"].isnull().values.all() and 'map_extension' in questions.columns:
            generate_profile(name ,questions)

def generate_profile(name, df_questions):
    print('processing profile {0}'.format(name))
    fullpath_extensions = get_resource_path("Extensions", name)
    fullpath_profiles = get_resource_path("Profiles", name)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    # Create the structure definition for the extensions 
    extensions, names = convert_df_to_extension_profiles(df_questions)
    #### Profiles for the rest of the resources ####
    #profiles = convert_df_to_profiles(name, df_questions)

    # write extensions to file¨
    for i in range (len(names)):
        fullpath_extensions = get_resource_path("Extensions", name+'-'+names[i])
        print("extension path" + fullpath_extensions)
        write_resource(fullpath_extensions, extensions[i], get_processor_cfg().encoding)
    # write profiles to file
    #write_resource(fullpath_profiles, profiles, get_processor_cfg().encoding)
    return 