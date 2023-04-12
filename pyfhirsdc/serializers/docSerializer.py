

"""
docs are list of this structure
{
    'type' : profile,
    'code' : id or path,
    'valueType' :data type,
    'description': decription
}
"""
import os
from pyfhirsdc.config import get_defaut_path, get_processor_cfg
from pyfhirsdc.serializers.utils import write_resource


def get_doc_title(name, desc):
    buffer = "#### {}\n\n".format(name)
    if desc is not None and desc != '': 
        buffer += "{}\n\n".format(desc)
    return buffer


def get_doc_table(name, desc, docs):
    buffer = ""
    if docs is not None:
        buffer += "#### {}\n\n".format(name)
        if desc is not None and desc != '': 
            buffer += "{}\n\n".format(desc)
        buffer += "| type | code / path | valueType | Description |\n|---|---|---|---|\n"
        for doc in docs:
            buffer += "| {} | {} | {} | {} |\n".format(doc['type'], doc['code'], doc['valueType'], doc['description'])
        buffer +="\n"

    return buffer 


def write_docs(buffer,name):
    filepath = os.path.join(get_processor_cfg().outputPath ,'pagecontent',name+".md")
    write_resource(filepath, buffer,'.md')
    