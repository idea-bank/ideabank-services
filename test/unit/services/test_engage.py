"""Tests for engagement queries"""

from datetime import datetime
from ideabank_webapi.services import EngagementDataService


def test_create_liking_query_builds():
    stmt = EngagementDataService.insert_liking("user", "user/concept")
    assert str(stmt) == 'INSERT INTO likes (display_name, concept_id) ' \
                        'VALUES (:display_name, :concept_id) ' \
                        'RETURNING likes.display_name, likes.concept_id'


def test_revoke_liking_query_builds():
    stmt = EngagementDataService.revoke_liking("user", "user/concept")
    assert str(stmt) == 'DELETE FROM likes ' \
                        'WHERE likes.display_name = :display_name_1 ' \
                        'AND likes.concept_id = :concept_id_1'


def test_check_liking_query_builds():
    stmt = EngagementDataService.check_liking("user", "user/concept")
    assert str(stmt) == 'SELECT likes.display_name, likes.concept_id \n' \
                        'FROM likes \n' \
                        'WHERE likes.display_name = :display_name_1 ' \
                        'AND likes.concept_id = :concept_id_1'


def test_create_following_query_builds():
    stmt = EngagementDataService.insert_following("user-a", "user-b")
    assert str(stmt) == 'INSERT INTO follows (follower, followee) ' \
                        'VALUES (:follower, :followee) ' \
                        'RETURNING follows.follower, follows.followee'


def test_unfollowing_query_builds():
    stmt = EngagementDataService.revoke_following("user-a", "user-b")
    assert str(stmt) == 'DELETE FROM follows ' \
                        'WHERE follows.followee = :followee_1 ' \
                        'AND follows.follower = :follower_1'


def test_check_following_query_builds():
    stmt = EngagementDataService.check_following("user-a", "user-b")
    assert str(stmt) == 'SELECT follows.follower, follows.followee \n' \
                        'FROM follows \n' \
                        'WHERE follows.follower = :follower_1 ' \
                        'AND follows.followee = :followee_1'


def test_create_comment_query_builds():
    stmt = EngagementDataService.create_comment(
            "user",
            "concept",
            "something to say",
            datetime.utcnow()
            )
    assert str(stmt) == 'INSERT INTO comments ' \
                        '(comment_id, comment_on, comment_by, free_text, parent, created_at) ' \
                        'VALUES (<next sequence value: comment_id_seq>, :comment_on, :comment_by, :free_text, :parent, :created_at) ' \
                        'RETURNING comments.comment_id'


def test_find_threads():
    stmt = EngagementDataService.top_level_comments("user/concept")
    assert str(stmt) == 'SELECT comments.comment_by, comments.free_text \n' \
                        'FROM comments \n' \
                        'WHERE comments.comment_on = :comment_on_1 ' \
                        'AND comments.parent IS NULL ' \
                        'ORDER BY comments.created_at'


def test_find_thread_members():
    stmt = EngagementDataService.comment_responses("user/concept", 69420)
    assert str(stmt) == 'SELECT comments.comment_by, comments.free_text \n' \
                        'FROM comments \n' \
                        'WHERE comments.comment_on = :comment_on_1 ' \
                        'AND comments.parent = :parent_1 ' \
                        'ORDER BY comments.created_at'
