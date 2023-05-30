"""Tests for concepts data service"""

from ideabank_webapi.services import ConceptsDataService


def test_account_has_all_parent_class_attributes():
    service = ConceptsDataService()
    expected = ['_query_buffer', '_query_results', '_session', '_s3_client']
    assert all(attr in service.__dict__ for attr in expected)


def test_concept_creation_query_builds():
    stmt = ConceptsDataService.create_concept(
            title='atitle',
            author='anauthor',
            description='adescription',
            diagram={'key': 'value'}
            )
    assert str(stmt) == 'INSERT INTO concepts ' \
                        '(title, author, description, diagram, created_at, updated_at) VALUES ' \
                        '(:title, :author, :description, :diagram, :created_at, :updated_at) ' \
                        'RETURNING concepts.identifier'


def test_concept_find_query_builds():
    stmt = ConceptsDataService.find_exact_concept('atitle', 'anauthor')
    assert str(stmt) == 'SELECT concepts.author, concepts.title, concepts.description,' \
                        ' concepts.diagram \n' \
                        'FROM concepts \nWHERE concepts.title = :title_1 AND concepts.author = :author_1'


def test_concept_linking_query_builds():
    stmt = ConceptsDataService.link_existing_concept('parentid', 'childid')
    assert str(stmt) == 'INSERT INTO concept_links (ancestor, descendant) ' \
                        'VALUES (:ancestor, :descendant) ' \
                        'RETURNING concept_links.ancestor, concept_links.descendant'
