import os

def write_resource(output_file, resource, encoding):
    output_file_path = os.path.join(output_file,resource.resource_type.lower()+\
        "-" + resource.id + "." + encoding)
    try: 
        output = open(output_file_path, 'w', encoding='utf-8')
        output.write(resource.json(indent=4)) if encoding == "json" \
            else  output.write(resource.xml())
        output.close()
    except:
        raise ValueError("Error writing resource: "+ resource.id)