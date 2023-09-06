from pyfhirsdc.converters.activityConverter import create_activity_propose_diagnosis

from pyfhirsdc.config import get_dict_df,get_processor_cfg
import pandas as pd
from pyfhirsdc.serializers.docSerializer import  write_docs
from pyfhirsdc.serializers.utils import get_resource_path, write_resource   
from pyfhirsdc.converters.libraryConverter import generate_library

def generate_conditions():
    dfs_conditions = get_dict_df()['conditions']
    doc_buffer = ""
    # generate the PD that will call Activity Definition (propose diagnose) base on the CQL
    for name, df_conditions in dfs_conditions.items():
        
        #pd = generate_conditions_pd(name ,df_conditions)
        library = generate_library(name, df_actions = df_conditions, type = 'c') 
        generate_conditions_activity_definition(name ,df_conditions,library)
        doc_buffer += "{{% include Activity{}.md %}}\n\n".format(name.capitalize())
    write_docs(doc_buffer,"AllActivities")

    
def generate_conditions_activity_definition(name ,df_conditions,library):
    for index, row in df_conditions.iterrows():
        if ('map_profile' in row and pd.notna(row['map_profile']) and  'SetCondition' in row['map_profile'] )or row['type'].strip() == 'condition':
            activity= create_activity_propose_diagnosis(row,library)
                # write file
            fullpath = get_resource_path("ActivityDefinition",activity.id)
            write_resource(fullpath, activity, get_processor_cfg().encoding)
    


def generate_conditions_pd(name ,df_conditions):
    pass

