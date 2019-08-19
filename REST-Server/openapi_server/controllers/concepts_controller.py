import connexion
import six

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server import util


def concept_mapping_concept_get(concept):  # noqa: E501
    """Get basic metadata information for a specified model.

    Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run. # noqa: E501

    :param concept: The name of a concept.
    :type concept: str

    :rtype: Concept
    """
    return 'do some magic!'


def list_concepts_get():  # noqa: E501
    """Obtain a list of available concepts

    Request a list of currently available concepts. These are derived from the list of  [UN indicators](https://github.com/WorldModelers/Ontologies/blob/master/performer_ontologies/un_to_indicators.tsv) and are tied to model output variables.  # noqa: E501


    :rtype: List[str]
    """
    return 'do some magic!'
