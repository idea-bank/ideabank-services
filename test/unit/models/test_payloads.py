"""Tests for payload models"""

import pytest
from ideabank_webapi.models import CreateConcept, AuthorizedPayload, AuthorizationToken
from pydantic import ValidationError


@pytest.fixture
def concept_structure():
    return {
            'title': 'example-title',
            'author': 'example author',
            'description': 'example description',
            'diagram': {
                        "nodes": [
                            {"id": 1, "label": "Board"},
                            {"id": 2, "label": "Truck"},
                            {"id": 3, "label": "Truck 2"},
                            {"id": 4, "label": "Wheel 1"},
                            {"id": 5, "label": "Wheel 2"},
                            {"id": 6, "label": "Wheel 3"},
                            {"id": 7, "label": "Wheel 4"}
                        ],
                        "edges": [
                            {"from": 1, "to": 2},
                            {"from": 1, "to": 3},
                            {"from": 2, "to": 4},
                            {"from": 2, "to": 5},
                            {"from": 3, "to": 6},
                            {"from": 3, "to": 7}
                        ]
                    }
            }


def test_concept_create_valid_structure(test_auth_token, concept_structure):
    CreateConcept(
            auth_token=test_auth_token,
            **concept_structure
            )


@pytest.mark.parametrize("bad_title", ['a', 300*'a', '\n\t\n\t\n\t\n\t'])
@pytest.mark.xfail(raises=ValidationError)
def test_concept_create_invalid_title(bad_title, test_auth_token, concept_structure):
    concept_structure['title'] = bad_title
    CreateConcept(
            auth_token=test_auth_token,
            **concept_structure
            )


@pytest.mark.xfail(raises=ValidationError)
def test_concept_create_invalid_diagram(test_auth_token, concept_structure):
    import math
    concept_structure['diagram'] = {
            x: math.sqrt(x)
            for x in map(lambda y: y*y, range(0, 25))
            }
    CreateConcept(
            auth_token=test_auth_token,
            **concept_structure
            )
