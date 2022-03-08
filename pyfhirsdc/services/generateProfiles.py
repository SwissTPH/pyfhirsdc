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
            generate_profile(name ,questions, df_profile)

def generate_profile(name, df_questions, df_profile):
    print('processing profile {0}'.format(name))
    if name == 'EmCare.B18-21.Sympto.2m.m':
        return
    fullpath_extensions = get_resource_path("Extensions", name)
    fullpath_profiles = get_resource_path("Profiles", name)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    # Create the structure definition for the extensions 
    extensions, names = convert_df_to_extension_profiles(df_questions)
    #### Profiles for the rest of the resources ####
    profiles, names_profiles = convert_df_to_profiles(df_questions, df_profile)
    # write extensions to file
    for i in range (len(names)):
        fullpath_extensions = get_resource_path("Extensions", name+'-'+names[i])
        print("extension path" + fullpath_extensions)
        write_resource(fullpath_extensions, extensions[i], get_processor_cfg().encoding)
    # write profiles to file
    print(len(names_profiles))
    if len(profiles)>0:
        for i in range(len(names_profiles)):
            fullpath_profiles = get_resource_path("Profiles", name+'-'+names_profiles[i])
            write_resource(fullpath_profiles, profiles[i], get_processor_cfg().encoding)
    return 