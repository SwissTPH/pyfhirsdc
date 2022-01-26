"""
Profile:http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire
Release: R4
Version: 4.0.1
"""
from fhir.resources.questionnaire import Questionnaire, QuestionnaireItem
from pydantic import Field
from fhir.resources import fhirtypes, fhirtypesvalidators
import typing

class QuestionnaireItemSDCType(fhirtypes.AbstractType):
    __resource_type__ = "QuestionnaireItemSDC"
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield getattr(fhirtypesvalidators,  "questionnaireitem_validator")

class QuestionnaireSDC(Questionnaire):
    design_note: fhirtypes.Markdown = Field(
        None,
        alias="designNote",
        title="The questionnaire - design note (as markdown)",
        description="Thedesign not of a questionnaire in markdown format.",
        # if property is element of this resource.
        element_property=True,
    )
    item: typing.List[QuestionnaireItemSDCType] = Field(
        None,
        alias="item",
        title="Questions and sections within the Questionnaire",
        description=(
            "A particular question, question grouping or display text that is part "
            "of the questionnaire."
        ),
        # if property is element of this resource.
        element_property=True,
    )
    sdc_questionnaire_preferred_terminology_server: fhirtypes.Uri = Field(
        None,
        alias="sdc-questionnaire-preferredTerminologyServer",
        title="Preferred terminology server for the questionnaire",
        description=(
            "A reference to a TerminologyServer that "
            "provides the  TerminologyService for the questionnaire."
        ),
        # if property is element of this resource.
        element_property=True,
    )

class QuestionnaireItemSDC(QuestionnaireItem):
    design_note: fhirtypes.Markdown = Field(
        None,
        alias="designNote",
        title="The questionnaire item - design note (as markdown)",
        description="Thedesign not of a questionnaire item in markdown format.",
        # if property is element of this resource.
        element_property=True,
    )
    sdc_questionnaire_preferred_terminology_server: fhirtypes.Uri = Field(
        None,
        alias="sdc-questionnaire-preferredTerminologyServer",
        title="Preferred terminology server for the questionnaire item",
        description=(
            "A reference to a TerminologyServer that "
            "provides the  TerminologyService for the questionnaire item."
        ),
        # if property is element of this resource.
        element_property=True,
    )
