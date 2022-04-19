"""
 convert dataframe to to fhir coding system concept

"""
from fhir.resources.codesystem import CodeSystemConcept, CodeSystemConceptProperty

from pyfhirsdc.converters.valueSetConverter import get_value_set_additional_data_keyword

def generate_questionnaire_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions.dropna(axis=0, subset=['id']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        concept.append(
            CodeSystemConcept(
                definition = question["description"],
                code = id,
                display =  question["label"]
            )
        )
    return concept


def generate_valueset_concept(df_value_set):
    concept = []
    # remove the line without id
    value_set = df_value_set[~df_value_set['code'].isin(
        get_value_set_additional_data_keyword()
        )]
    value_set = value_set.dropna(axis=0, subset=['code']).set_index('code').to_dict('index')
    # remove the line without id
    for code, question in value_set.items():
        concept.append(
            CodeSystemConcept(
                definition = question["definition"],
                code = code,
                display =  question["display"]
            )
        )
    return concept

def generate_anthro_valueset_concept(row, codeColumn):
    if "sex" in row and codeColumn in row and "l" in row and "s" in row and "m" in row: 
        sex = row["sex"]
        l = row["l"]
        m = row["m"]
        s = row["s"]
        codeColumnValue = row[codeColumn]
        codeColumnValue = int(codeColumnValue) if codeColumn == "age" else codeColumnValue 
        definition = "anthro data for sex: %d, %s: %d l: %d, m: %d, s: %d " % (sex, codeColumn, codeColumnValue, l, m, s)  
        properties = [
            CodeSystemConceptProperty(code = "l", valueDecimal = l),
            CodeSystemConceptProperty(code = "m", valueDecimal = m),
            CodeSystemConceptProperty(code = "s", valueDecimal = s),        
            CodeSystemConceptProperty(code = "sex", valueString = "male" if sex == 1 else "female"),        
            CodeSystemConceptProperty(code = codeColumn, valueDecimal = codeColumnValue),        
        ]      
        return CodeSystemConcept(
            definition = definition,
            code = str(int(sex)) + "-" + str(codeColumnValue),
            display =  definition,
            property = properties 
        )
    else:
        return None
        

def generate_anthro_valueset_concepts(df):
    # make sure indexes pair with number of rows
    df.reset_index()
    concepts = []
    codeColumn = "age"
    # generate code
    # rename df colum age to codeColumn
    if 'age' in df.columns:
        codeColumn = "age"
    # rename df colum height to codeColumn
    elif 'height' in df.columns:
        codeColumn = "height"
    # rename df colum length to codeColumn
    elif 'length' in df.columns:
        codeColumn = "length"        
    for index, row in df.iterrows():
        concept = generate_anthro_valueset_concept(row, codeColumn)
        if concept is not None:
            concepts.append(concept)
    return concepts