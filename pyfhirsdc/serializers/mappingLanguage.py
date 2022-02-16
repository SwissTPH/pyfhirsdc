"""
Serializer to write the map file from a StructureMAp where 
the mapping language is define in the rule description

"""


from pyfhirsdc.serializers.utils import write_resource


def write_mapping_file(filepath, structure_map):

    write_resource(
        filepath,
        get_mapping_file_header(structure_map)\
            + get_mapping_file_groups(structure_map) 
        , 'map'
        )


def get_mapping_file_header(structure_map):

    # structure map def
    header = "map '" + structure_map.url + "'='" + structure_map.id + "'\n\n"
    # get the source / Source
    for in_output in structure_map.structure:
        header = header + "uses '" + in_output.url + "' alias "\
             + in_output.alias + " as " + in_output.mode + "\n"
    
    return header

def get_mapping_file_groups(structure_map):
    group_buffer = ''
    for group in structure_map.group:
        group_buffer = group_buffer + get_mapping_file_group(group)
    return group_buffer


def get_mapping_file_group(group):
    group_buffer = 'group  ' + group.name + "{\n"
    i = 0
    for in_output in group.input:
        group_buffer = group_buffer + "\t" + in_output.mode + " "\
             + in_output.name + " : " + in_output.type 
        group_buffer = group_buffer + ",\n" if i < len(group.input)\
             else "\n"
        i+=1
    group_buffer += "} {\n"
    # write Items subsection
    if group.rule is not None and group.rule != [] :
        group_buffer = group_buffer + "\t" + "qr.item as item then {\n"
        # write item mapping
        for rule in group.rule:
            group_buffer = group_buffer + "\t\t" +  rule.documentation + "'" + rule.name + "'\n"
        # close Items subsection 
        group_buffer = group_buffer + "\t}\n"  
    # close group
    group_buffer = group_buffer + "}\n\n"
        
    
    return group_buffer
