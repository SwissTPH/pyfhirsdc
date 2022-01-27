import sys, getopt
from pyfhirsdc.services.processInputFile import process_input_file

if __name__ == "__main__":
    bundle = False
    output = False
    library = False
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hlob:c:",["conf=","help"])
    except getopt.GetoptError:
        print('main.py -c config_file_path')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('main.py -c config_file_path')
            sys.exit()
        elif opt in ("-c", "--conf"):
            conf = arg
        elif opt == "-b":
            bundle = True
        elif opt == "-o":
            output = True
        elif opt == "-l":
            library = True
    if output:
        process_input_file(conf) # output is the default output directory
    if library:
        # compress CQL
        # update Libraries
        pass
    if bundle:
        # bundle everything
        pass
