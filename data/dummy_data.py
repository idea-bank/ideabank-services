"""
    :module name: dummy_data
    :module summary: a little python script to generate fake data for testing
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

from faker import Faker
from password_generator import PasswordGenerator
import secrets
import hashlib
import datetime
import random
import csv
import json

pwo = PasswordGenerator()

fake = Faker()


class FakeAccount:
    def __eq__(self, other):
        return self.display_name == other.display_name

    def __init__(self):
        password = pwo.generate()
        self.display_name = fake.domain_word()
        self.preferred_name = fake.name()
        self.biography = ' '.join(fake.paragraphs())
        self.salt_value = secrets.token_hex()
        self.password_hash = hashlib.sha256(
                f'{password}{self.salt_value}'.encode('utf-8')
                ).hexdigest()
        self.created_at = fake.date_time_this_year(tzinfo=datetime.timezone.utc)
        self.updated_at = fake.date_time_between_dates(
                self.created_at,
                datetime.datetime.now(tz=datetime.timezone.utc),
                datetime.timezone.utc
                )
        print(f"Fake account: {self.display_name}")

    def __hash__(self):
        return hash(self.display_name)


class FakeConcept:
    DEFAULT_COMPONENT_GRAPH = {
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

    def __eq__(self, other):
        return self.author == other.author and \
                self.title == other.title

    def __hash__(self):
        return hash(f'{self.author}/{self.title}')

    def __init__(self, users):
        account = random.choice(users)
        self.title = '-'.join(fake.words(unique=True))
        self.author = account.display_name
        self.description = ' '.join(fake.paragraphs())
        self.diagram = json.dumps(self.DEFAULT_COMPONENT_GRAPH)
        self.created_at = fake.date_time_between_dates(
                account.created_at,
                datetime.datetime.now(tz=datetime.timezone.utc),
                datetime.timezone.utc
                )
        self.updated_at = fake.date_time_between_dates(
                self.created_at,
                datetime.datetime.now(tz=datetime.timezone.utc),
                datetime.timezone.utc
                )
        print(f"Fake concept: {self.author}/{self.title}")


class FakeLink:
    def __eq__(self, other):
        return self.ancestor == other.ancestor and \
                self.descendant == other.descendant

    def __hash__(self):
        return hash((self.ancestor, self.descendant))

    def __init__(self, concepts):
        concept1 = random.choice(concepts)
        concept2 = random.choice(concepts)
        if concept1 == concept2:
            raise ValueError('Cannot link concept to itself')
        if concept2.created_at >= concept1.created_at:
            raise ValueError('Cannot make child before parent')
        self.ancestor = f'{concept1.author}/{concept1.title}'
        self.descendant = f'{concept2.author}/{concept2.title}'
        print(f"Fake Link: {self.ancestor} <- {self.descendant}")


account_rows = set()
concept_rows = set()
link_rows = set()

while len(account_rows) < 1000:
    account_rows.add(FakeAccount())


while len(concept_rows) < 10000:
    concept_rows.add(FakeConcept(list(account_rows)))

while len(link_rows) < 5000:
    try:
        link_rows.add(FakeLink(list(concept_rows)))
    except ValueError as err:
        print(str(err))

with open('test_accounts.csv', newline='', mode='w') as accounts_csv:
    accounts_writer = csv.writer(accounts_csv, quotechar="'", delimiter='|')
    for account in account_rows:
        row = [
                account.display_name,
                account.preferred_name,
                account.biography,
                account.password_hash,
                account.salt_value,
                account.created_at.isoformat(),
                account.updated_at.isoformat()
                ]
        accounts_writer.writerow(row)

with open('test_concepts.csv', newline='', mode='w') as concepts_csv:
    concept_writer = csv.writer(concepts_csv, quotechar="'", delimiter='|')
    for concept in concept_rows:
        row = [
                concept.author,
                concept.title,
                concept.description,
                concept.diagram,
                concept.created_at.isoformat(),
                concept.updated_at.isoformat()
                ]
        concept_writer.writerow(row)

with open('test_links.csv', newline='', mode='w') as links_csv:
    link_writer = csv.writer(links_csv, quotechar="'", delimiter='|')
    for link in link_rows:
        row = [link.ancestor, link.descendant]
        link_writer.writerow(row)
