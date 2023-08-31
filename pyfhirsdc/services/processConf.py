from pyfhirsdc.serializers.json import read_file 
import semantic_version
import json
def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__

# this function updates the build number in the configuration file and the library version incrementally 
# this is dependent on the developer vs production environment
# in development the patch version is update
# in production the minor version is updated
# TODO: Decide on a way for major version number update

def updateBuildNumber(filePath):
    obj_conf = read_file(filePath)
    
    

    # get build environment
    env =  obj_conf.processor.environment
    lib_version = obj_conf.fhir.lib_version 
    # convert the version into semantic version 
    v = semantic_version.Version.coerce(lib_version)
    # if mode is development increase patch version
    # if mode is production increase minor version
    v.prerelease = []
    if env == "staging":
        new_v = v.next_patch()
        new_build_number = 0 
        
    elif env == "prod":
        new_v = v.next_minor()
        new_build_number = 0
    else:#dev
        new_build_number = obj_conf.processor.build + 1
        new_v  = v
        new_v.prerelease = ('alpha',str(new_build_number))
    # update the lib version to new version
    obj_conf.processor.build = new_build_number
    obj_conf.fhir.lib_version = str(new_v)

    new_build_json = json.dumps(obj_conf, default=dumper, indent=4)

    open_conf_file = open(filePath, "w")
    open_conf_file.write(new_build_json)
    open_conf_file.close()