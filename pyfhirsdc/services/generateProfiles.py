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
from pyfhirsdc.converters.profileConverter import convert_df_to_profiles
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")

def generate_profiles():
    logger.info('processing profiles.................')

    #### Profiles for the rest of the resources ####
    profiles = convert_df_to_profiles()
    # write profiles to file
    if len(profiles)>0:
        for profile in profiles:
            logger.info( "Saving structureDefinition %s", profile.name)
            fullpath_profiles = get_resource_path("StructureDefinition",profile.name)
            write_resource(fullpath_profiles, profile, get_processor_cfg().encoding)
    return 