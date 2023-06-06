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
import os
import shutil
import uuid
from PIL import Image


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


def create_rectangle(width, height, color, output_file):
    # Create a new image with the specified dimensions
    image = Image.new("RGB", (width, height), color)

    # Save the image as a PNG file
    image.save(output_file, "PNG")
    print(f"Rectangle image saved as {output_file}")


class FakeLike:
    def __eq__(self, other):
        return self.display_name == other.display_name and \
                self.concept_id == other.concept_id

    def __hash__(self):
        return hash((self.display_name, self.concept_id))

    def __init__(self, concept, like_pool):
        liker = random.choice(like_pool)
        self.concept_id = f'{concept.author}/{concept.title}'
        self.display_name = liker.display_name
        print(f"Fake like: {self.concept_id} <- {self.display_name}")


class FakeFollow:
    def __eq__(self, other):
        return self.follower == other.follower and \
                self.followee == other.followee

    def __hash__(self):
        return hash((self.follower, self.followee))

    def __init__(self, user, follow_pool):
        follower = random.choice(follow_pool)
        if user == follower:
            raise ValueError("Cannot follow self")
        self.follower = follower.display_name
        self.followee = user.display_name
        print(f"Fake follow: {self.followee} <- {self.follower}")


class FakeComment:
    def __eq__(self, other):
        return self.comment_id == other.comment_id

    def __hash___(self):
        return hash(self.comment_id)

    def __init__(self, concept, commenter_pool, parent_comment=None):
        commenter = random.choice(commenter_pool)
        earlier_possible_timestamp = max(
                concept.created_at,
                commenter.created_at,
                parent_comment.created_at if parent_comment else datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
                )
        if earlier_possible_timestamp < commenter.created_at:
            raise ValueError("Account cannot comment before creation")
        self.comment_id = uuid.uuid4()
        self.comment_on = f'{concept.author}/{concept.title}'
        self.comment_by = commenter.display_name
        self.parent = parent_comment.comment_id if parent_comment else None
        self.comment_text = fake.sentence()
        self.created_at = fake.date_time_between_dates(
                earlier_possible_timestamp,
                datetime.datetime.now(tz=datetime.timezone.utc),
                datetime.timezone.utc
                )
        print(f"Fake comment: {self.comment_by} commented on {self.comment_on}")


account_rows = set()
concept_rows = set()
link_rows = set()
like_rows = set()
follow_rows = set()
comment_rows = list()

while len(account_rows) < 1000:
    account_rows.add(FakeAccount())


while len(concept_rows) < 10000:
    concept_rows.add(FakeConcept(list(account_rows)))

while len(link_rows) < 5000:
    try:
        link_rows.add(FakeLink(list(concept_rows)))
    except ValueError as err:
        print(str(err))


for concept in concept_rows:
    thread_count = random.randint(0, 5)
    reponse_count = thread_count
    for _ in range(thread_count):
        print("build thread #", _)
        while True:
            try:
                new_comment = FakeComment(concept, list(account_rows))
                comment_rows.append(new_comment)
            except ValueError as err:
                print(str(err))
                continue
            break
        while reponse_count > 0:
            print("Responses:", reponse_count)
            for existing_comment in comment_rows:
                while True:
                    try:
                        comment_rows.extend(
                                [
                                    FakeComment(concept, list(account_rows), existing_comment)
                                    for _ in range(random.randint(0, reponse_count))
                                    ]
                                )
                    except ValueError as err:
                        print(str(err))
                        continue
                    break
            reponse_count = reponse_count // 2


for concept in concept_rows:
    like_count = random.randint(0, 55)
    this_concepts_likes = set()
    while len(this_concepts_likes) < like_count:
        this_concepts_likes.add(FakeLike(concept, list(account_rows)))
    like_rows = like_rows.union(this_concepts_likes)


for account in account_rows:
    follower_count = random.randint(0, 55)
    this_users_followers = set()
    while len(this_users_followers) < follower_count:
        try:
            this_users_followers.add(FakeFollow(account, list(account_rows)))
        except ValueError as err:
            print(str(err))
    follow_rows = follow_rows.union(this_users_followers)


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

with open('test_comments.csv', newline='', mode='2') as comments_csv:
    comment_writer = csv.writer(comments_csv, quotechar="'", delimiter='|')
    for comment in comment_rows:
        row = [
                str(comment.comment_id),
                comment.comment_on,
                comment.comment_by,
                comment.comment_text,
                str(comment.parent) if comment.parent else 'NULL',
                comment.created_at.isoformat()
                ]
        comment_writer.writerow(row)

with open('test_links.csv', newline='', mode='w') as links_csv:
    link_writer = csv.writer(links_csv, quotechar="'", delimiter='|')
    for link in link_rows:
        row = [link.ancestor, link.descendant]
        link_writer.writerow(row)


with open('test_likes.csv', newline='', mode='w') as likes_csv:
    likes_writer = csv.writer(likes_csv, quotechar="'", delimiter='|')
    for like in like_rows:
        row = [like.display_name, like.concept_id]
        likes_writer.writerow(row)


with open('test_follows.csv', newline='', mode='w') as follows_csv:
    follows_writer = csv.writer(follows_csv, quotechar="'", delimiter='|')
    for follow in follow_rows:
        row = [follow.follower, follow.followee]
        follows_writer.writerow(row)


with open('test_accounts.csv', newline='', mode='r') as accounts_csv:
    accounts_reader = csv.reader(accounts_csv, quotechar="'", delimiter='|')
    if os.path.exists('./avatars'):
        shutil.rmtree('./avatars')
    os.mkdir('./avatars')
    for row in accounts_reader:
        height, width = 200, 200
        color = tuple(random.randint(0, 255) for _ in range(3))  # random RGB tuple
        create_rectangle(width, height, color, f'avatars/{row[0]}')

with open('test_concepts.csv', newline='', mode='r') as concepts_csv:
    concepts_reader = csv.reader(concepts_csv, quotechar="'", delimiter='|')
    if os.path.exists('thumbnails/'):
        shutil.rmtree('thumbnails/')
    for row in concepts_reader:
        os.makedirs(f'thumbnails/{row[0]}', exist_ok=True)
        height, width = 400, 800
        color = tuple(random.randint(0, 255) for _ in range(3))  # random RGB tuple
        create_rectangle(width, height, color, f'thumbnails/{row[0]}/{row[1]}')
