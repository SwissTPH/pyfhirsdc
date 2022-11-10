"""
    Service to generate the libraries ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""


import numpy as np

from pyfhirsdc.config import get_dict_df
from pyfhirsdc.serializers.librarySerializer import generate_library


def generate_libraries():
    dfs_library = get_dict_df()['libraries']

    for name, df_questions in dfs_library.items():
        generate_library(name, df_questions,'q')








