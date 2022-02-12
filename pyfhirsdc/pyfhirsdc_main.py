import sys, getopt
#from data_dictionnary.processor import process_data_dicitonnary_table_sheet

if __name__ == "__main__": 
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hi:d:c:o:",["conf=","help"])
    except getopt.GetoptError:
        print('processDataDictionnary.py -c config_file_path')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('processDataDictionnary.py -c config_file_path')
            sys.exit()
        elif opt in ("-c", "--conf"):
            conf = arg
    #process_data_dicitonnary_table_sheet(conf) # output is the default output directory
