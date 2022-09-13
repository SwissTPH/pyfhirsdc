"""
    Service to generate the Structure definition (profiles)
    needs the sheet:
        - profiles
        - q.X
"""

#from tkinter.font import names

from pyfhirsdc.config import  get_dict_df, get_processor_cfg
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource
from pyfhirsdc.converters.profileConverter import  init_extension_def
from pyfhirsdc.converters.profileConverter import convert_df_to_profiles
import pandas as pd 


def generate_profiles():


    generate_extension()
    ## Concat all the dataframes together so that we can create the profiles based on it 
    ## instead of going through sheets one by one
    
    generate_profile()


def generate_extension():
    print('processing extenstions ')

    dfs_questionnaire = get_dict_df()['questionnaires']
    all_questionnaires = pd.concat(dfs_questionnaire, ignore_index=True)

    # clean the data frame
    all_questionnaires = all_questionnaires.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_extension']).set_index('id')
    # Create the structure definition for the extensions 
    for idx, row in all_questionnaires.iterrows():
        extension = init_extension_def(row)
        fullpath_extensions = get_resource_path("Extensions", extension.name, get_processor_cfg().encoding, False )
        write_resource(fullpath_extensions, extension, get_processor_cfg().encoding)

    # write extensions to file


def generate_profile():
    print('processing profiles.................')
    # clean the data frame

    #### Profiles for the rest of the resources ####
    profiles, names_profiles = convert_df_to_profiles()
    # write profiles to file
    print(len(names_profiles))
    if len(profiles)>0:
        for i in range(len(names_profiles)):
            fullpath_profiles = get_resource_path("Profiles",names_profiles[i])
            write_resource(fullpath_profiles, profiles[i], get_processor_cfg().encoding)
    return 