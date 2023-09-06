import getopt
import logging, coloredlogs
import sys

from pyfhirsdc.services.generateBundle import write_bundle
from pyfhirsdc.services.processInputFile import process_input_file, process_data_dictionary_file, process_decision_support_logic_file
from pyfhirsdc.services.processLibraries import process_libraries
from pyfhirsdc.services.uploadFiles import upload_files
from pyfhirsdc.services.processConf import updateBuildNumber

def print_help():
    print('-c / --conf config_file_path')
    print('-o to generate fhir resources')
    print('-h / --help to generate this message')
    print('-b to bundle the fhir ressource int the output path')
    print('-l to build the library with cql in base64')
    print('--anthro to generate the antro code system from tsv files (files can be found here https://github.com/WorldHealthOrganization/anthro/tree/master/data-raw/growthstandards)')


   
def setup_logger(logger_name,
                 log_file, 
                 level=logging.INFO, 
                 formatting  ='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'):
     
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter(formatting)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(formatter)
    #stream_handler = logging.StreamHandler()
    #stream_handler.setFormatter(formatter)
    coloredlogs.install()
    l.setLevel(level)
    l.addHandler(file_handler)


setup_logger('default', "debug.log", logging.DEBUG)
logger = logging.getLogger('default')


if __name__ == "__main__":
    bundle = False
    output = False
    library = False
    #anthro = False
    upload = False
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hlobuc:",["conf=","help","anthro"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_help()
            sys.exit()
        elif opt in ("-c", "--conf"):
            conf = arg
        elif opt == "-b":
            bundle = True
        elif opt == "-o":
            output = True
        elif opt == "--anthro":
            anthro = True
        elif opt == "-l":
            library = True
        elif  opt == "-u":
            upload = True 
    #if anthro:
    #    generate_anthro_codesystems(conf)

    # thorw an error when conf file is not provided 
    # if conf file is provided update the conf file build number and library version
    if not conf:
        raise Exception("No configuration file provided")
    else:
        updateBuildNumber(conf)        

    if output:
        logger.info("Process input file")
        process_input_file(conf) # output is the default output directory
        logger.info("Process data dictionary file")
        process_data_dictionary_file(conf)
        logger.info("Processing decision logic file")
        process_decision_support_logic_file(conf)
    if library:
        # compress CQL
        logger.info("Process libraries")
        process_libraries(conf)
        # update Libraries
        pass
    if bundle:
        logger.info("Write bundle")
        # bundle everything
        write_bundle(conf)
    if upload:
        upload_files(conf, bundle)
        
