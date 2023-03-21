"""
    :module_name: test_function
    :module_summary: #TODO
    :module_author: #TODO
"""

import json
import unittest
from function import handler
from ideadb_handler import *

MOCK_DATA_FILE = "./mock_data.json"

class SimplePostViewTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SimplePostViewTests, self).__init__(*args, **kwargs)
        self.posts = IdeaPostTable()

    def get_mock_data(self):
        contents = None
        with open(MOCK_DATA_FILE, 'r') as data_file:
            contents = json.loads(data_file.read())
        return contents
    
    def setup(self):
        post_mock_data = self.get_mock_data()
        for post in post_mock_data:
            self.posts.add_post(post)

    def test_get_nonexistant_post(self):
        response = handler({'body': {'IdeaPostID': '100', 'IdeaAuthorID': '100'}}, {})
        self.assertEqual(json.loads(response['body']), {})
        
    def test_get_actual_post(self):
        post_mock_data = self.get_mock_data()
        
        post = post_mock_data[0]
        response = handler({'body': post}, {})
        self.assertIn('body',response)
        self.assertEqual(json.loads(response['body'])['IdeaPostID'], {'S': post['IdeaPostID']})
        self.assertEqual(json.loads(response['body'])['IdeaAuthorID'], {'S': post['IdeaAuthorID']})

if __name__ == '__main__':
    unittest.main()
