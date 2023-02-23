"""
    Service to generate the Structure definition (profiles)
    needs the sheet:
        - profiles
        - q.X
"""

#from tkinter.font import names
import logging

import pandas as pd 

from pyfhirsdc.config import get_dict_df, get_processor_cfg
from pyfhirsdc.converters.profileConverter import (convert_df_to_profiles)
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")

def generate_profiles():
    logger.info('processing profiles.................')

    #### Profiles for the rest of the resources ####
    profiles, names_profiles = convert_df_to_profiles()
    # write profiles to file
    logger.info(len(names_profiles))
    if len(profiles)>0:
        for i in range(len(names_profiles)):
            fullpath_profiles = get_resource_path("Profiles",names_profiles[i])
            write_resource(fullpath_profiles, profiles[i], get_processor_cfg().encoding)
    return 