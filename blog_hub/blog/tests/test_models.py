from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from blog.models import Comment, Post
from blog.tests.factories import make_comment, make_post, make_user


class PostModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_str_is_title(self):
        post = make_post(self.user, title='Hello world')
        self.assertEqual(str(post), 'Hello world')

    def test_new_post_is_a_draft_by_default(self):
        post = Post.objects.create(author=self.user, title='Draft', text='...')
        self.assertIsNone(post.published_date)

    def test_create_date_defaults_to_now(self):
        before = timezone.now()
        post = Post.objects.create(author=self.user, title='T', text='...')
        self.assertGreaterEqual(post.create_date, before)
        self.assertLessEqual(post.create_date, timezone.now())

    def test_publish_sets_published_date_and_saves(self):
        post = make_post(self.user, published=False)
        before = timezone.now()

        post.publish()

        post.refresh_from_db()
        self.assertIsNotNone(post.published_date)
        self.assertGreaterEqual(post.published_date, before)

    def test_publish_again_moves_the_date_forward(self):
        post = make_post(self.user, published=False)
        post.published_date = timezone.now() - timedelta(days=3)
        post.save()

        post.publish()

        self.assertGreater(post.published_date, timezone.now() - timedelta(minutes=1))

    def test_approve_comments_returns_only_approved(self):
        post = make_post(self.user)
        approved = make_comment(post, approved=True)
        make_comment(post, approved=False)

        self.assertQuerySetEqual(post.approve_comments(), [approved])

    def test_approve_comments_ignores_other_posts(self):
        post = make_post(self.user)
        other = make_post(self.user, title='Other')
        make_comment(other, approved=True)

        self.assertEqual(post.approve_comments().count(), 0)

    def test_get_absolute_url_points_to_detail(self):
        post = make_post(self.user)
        self.assertEqual(post.get_absolute_url(), f'/post/{post.pk}/')

    def test_deleting_author_deletes_posts(self):
        make_post(self.user)
        self.user.delete()
        self.assertEqual(Post.objects.count(), 0)


class CommentModelTests(TestCase):
    def setUp(self):
        self.post = make_post(make_user())

    def test_str_is_author(self):
        comment = make_comment(self.post, author='Ana')
        self.assertEqual(str(comment), 'Ana')

    def test_new_comment_is_not_approved(self):
        comment = Comment.objects.create(post=self.post, author='A', text='B')
        self.assertFalse(comment.approved_comment)

    def test_approve_sets_flag_and_saves(self):
        comment = make_comment(self.post)

        comment.approve()

        comment.refresh_from_db()
        self.assertTrue(comment.approved_comment)

    def test_get_absolute_url_points_to_its_post(self):
        comment = make_comment(self.post)
        self.assertEqual(comment.get_absolute_url(), f'/post/{self.post.pk}/')

    def test_comments_are_reachable_from_post(self):
        comment = make_comment(self.post)
        self.assertQuerySetEqual(self.post.comments.all(), [comment])

    def test_deleting_post_deletes_comments(self):
        make_comment(self.post)
        self.post.delete()
        self.assertEqual(Comment.objects.count(), 0)
