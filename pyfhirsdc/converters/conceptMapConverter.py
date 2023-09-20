from fhir.resources.R4B.conceptmap import ConceptMap
from fhir.resources.R4B.fhirtypes import Code


# Given a code system, will create a concept map for that code system
def get_concept_map_for_system(canonical_base,code_system_label,concept_maps,system_URL):
    concept_map = concept_maps.get(system_URL)
    if concept_map:
        if code_system_label:
            cm = ConceptMap.construct()
            cm.id = code_system_label
            cm.url = "{0}/ConceptMap/{1}" \
            .format(canonical_base, code_system_label)
            cm.name = code_system_label
            cm.title = "{0}".format(code_system_label)
            cm_code = Code("status")
            cm.status = cm_code
            cm.experimental= False
            cm.description = "Concept mapping from content extended codes to {0}".format(code_system_label)
            concept_maps[system_URL] = cm

    return cm, concept_maps