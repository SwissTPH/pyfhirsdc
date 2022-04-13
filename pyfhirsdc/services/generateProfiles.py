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


def generate_profiles(dfs_questionnaire, df_profile, df_valuesets):
    
    all_dataframes = pd.concat(dfs_questionnaire).dropna(axis=0, subset=['map_extension'])
    
    generate_extension(all_dataframes, df_profile)
    ## Concat all the dataframes together so that we can create the profiles based on it 
    ## instead of going through sheets one by one
    #all_questionnaires = pd.concat(all_dataframes, ignore_index=True)
    generate_profile(all_dataframes, df_profile, df_valuesets)
    
def generate_extension(df_questions, df_profile):
    print('processing extenstions ')

    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    # Create the structure definition for the extensions 
    extensions, names = convert_df_to_extension_profiles(df_questions)
    # write extensions to file
    for i in range (len(names)):
        fullpath_extensions = get_resource_path("Extensions", names[i])
        print("extension path" + fullpath_extensions)
        write_resource(fullpath_extensions, extensions[i], get_processor_cfg().encoding)
    return 

def generate_profile(df_questions, df_profile, df_valuesets):
    print('processing profiles.................')
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    #### Profiles for the rest of the resources ####
    profiles, names_profiles = convert_df_to_profiles(df_questions, df_profile, df_valuesets)
    # write profiles to file
    print(len(names_profiles))
    if len(profiles)>0:
        for i in range(len(names_profiles)):
            fullpath_profiles = get_resource_path("Profiles",names_profiles[i])
            write_resource(fullpath_profiles, profiles[i], get_processor_cfg().encoding)
    return 