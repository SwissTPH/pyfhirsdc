import logging
import os
import shutil
import ctypes
    


from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.R4B.identifier import Identifier

from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg, read_config_file
from pyfhirsdc.models.questionnaireSDC import QuestionnaireSDC
from pyfhirsdc.serializers.json import read_file, read_resource
from pyfhirsdc.serializers.utils import write_resource

logger = logging.getLogger("default")    
    
def write_bundle(conf):
    exclude_folders = get_processor_cfg().bundle_exclude_paths if hasattr(get_processor_cfg(), 'bundle_exclude_paths') else []

    scope = get_processor_cfg().scope if get_processor_cfg().scope is not None else "Unknown"
    bundle = Bundle( identifier = Identifier(value = scope + "Bundle"),
                type  = 'batch', entry = [])
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        folderdir = get_processor_cfg().outputPath
        # giving file extensions
        ext = ('.json')
        # iterating over directory and subdirectory to get desired result
        dirs = []  
        for path, dirc, files in os.walk(folderdir, topdown=True):
            dirs[:] = [d for d in dirc if d not in exclude_folders]

#TODO: Find a workaround to remove the nested for loops if it is possible 
        for path, dirs, files in dirs:
            for name in files:
                if name.endswith(ext) and not name.startswith("bundle"):
                    logger.debug('{}{}{}{}'.format(conf, path, dirc , name)) # printing file name
                    add_resource(path,name,bundle)        
                        
    bundle_name = os.path.join(folderdir,'bundle-{}.json'.format(get_fhir_cfg().lib_version))
    std_name = os.path.join(folderdir,'bundle.json')
    write_resource(bundle_name, bundle)
    if os.path.lexists(std_name):
        os.remove(std_name)
    if os.name == 'nt':
        kdll = ctypes.windll.LoadLibrary("kernel32.dll")
        kdll.CreateSymbolicLinkA(bundle_name, std_name, 0)
    else:
        os.symlink(bundle_name, std_name)
                    
def add_resource(path,name,bundle):
    file_path = os.path.join(path,name)
    ressource_dict = read_resource(file_path, 'any')
    if ressource_dict is not None and 'resourceType' in ressource_dict and 'url' in ressource_dict and ressource_dict['resourceType'] !='ImplementationGuide':
        
        bundle.entry.append(
            BundleEntry(
                fullUrl = ressource_dict['url'],
                request = BundleEntryRequest(
                    method  = 'PUT',
                    url =  ressource_dict['resourceType'] + '/' + ressource_dict['id']      
                ),
                resource= QuestionnaireSDC.parse_raw( read_file(file_path, type = "str")) if ressource_dict['resourceType'] == 'Questionnaire' else read_file(file_path, type = "str")
            )
        )