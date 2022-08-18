
def build_plan_definition_index(planDefinitions):
    index =  "### Plan Definitions by Decision ID\n\n "+\
    "|Decision Table|Description| \n "+"|---|---|\n "
    for key, plan_definition in planDefinitions.items():
        index += "|[{0}](PlanDefinition-{1}.html)|{2}|".format(\
            plan_definition.title, plan_definition.id, 
            plan_definition.description)
        index += "\n "
    return index


def write_plan_definition_index(planDefinitions, output_path):
    output = open(output_path+"PlanDefinitionIndex.md", 'w')
    output.write(build_plan_definition_index(planDefinitions))