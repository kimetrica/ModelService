# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server.test import BaseTestCase


class TestConceptsController(BaseTestCase):
    """ConceptsController integration test stubs"""

    def test_concept_mapping_concept_get(self):
        """Test case for concept_mapping_concept_get

        Get an array of models related to a concept.
        """
        response = self.client.open(
            '/concept_mapping/{Concept}'.format(concept='concept_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_concepts_get(self):
        """Test case for list_concepts_get

        Obtain a list of available concepts
        """
        response = self.client.open(
            '/list_concepts',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
