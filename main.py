import sys, getopt
from pyfhirsdc.services.generateCodeSystem import generate_anthro_codesystems
from pyfhirsdc.services.processInputFile import process_input_file

def print_help():
    print('-c / --conf config_file_path')
    print('-o to generate fhir ressoruces')
    print('-h / --help to generate this message')
    print('-b to bundle the fhir ressource int the output path')
    print('-l to build the library with cql in base64')
    print('--anthro to generate the antro code system from tsv files (files can be found here https://github.com/WorldHealthOrganization/anthro/tree/master/data-raw/growthstandards)')
    

if __name__ == "__main__":
    bundle = False
    output = False
    library = False
    anthro = False
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hlob:c:",["conf=","help","anthro"])
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
    if anthro:
        generate_anthro_codesystems(conf)
    if output:
        process_input_file(conf) # output is the default output directory
    if library:
        # compress CQL
        # update Libraries
        pass
    if bundle:
        # bundle everything
        pass


    