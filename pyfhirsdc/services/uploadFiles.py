# importing the module
import os
from pyfhirsdc.config import  get_fhir_cfg, get_processor_cfg,  read_config_file
import re
from pyfhirsdc.serializers.http import put_files

from pyfhirsdc.serializers.json import read_resource 
 
def upload_files (conf, bundle):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        folderdir = get_processor_cfg().outputPath
        # giving file extensions
        ext = ('.json')
        # iterating over directory and subdirectory to get desired result
        for path, dirc, files in os.walk(folderdir):
            for name in files:
                if name.endswith(ext):
                    print(conf, path, dirc, name)  # printing file name
                    upload_file(conf, path, name)


 
def upload_file(conf, path, name):
    file_path = os.path.join(path,name)
    ressource_dict = read_resource(file_path, 'any')
    if ressource_dict is not None:
        if 'url' in ressource_dict:
            url = ressource_dict['url']
            if url.startswith(get_fhir_cfg().canonicalBase):
                put_files(file_path, url)
        else:
            print("ressource {0} doesn't have a URL".format(file_path) )