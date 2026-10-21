from django.test import TestCase
from django.urls import reverse

from blog.models import Comment
from blog.tests.factories import make_comment, make_post, make_user

LOGIN_URL = reverse('login')


class AddCommentViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user, title='Commented post')
        self.url = reverse('blog:add_comment_to_post', args=[self.post.pk])

    def test_visitor_can_open_the_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/comment/comment_form.html')
        self.assertContains(response, 'Commented post')

    def test_visitor_can_comment(self):
        response = self.client.post(self.url, {'author': 'Ana', 'text': 'Great!'})

        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.pk]))
        comment = Comment.objects.get()
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, 'Ana')
        self.assertFalse(comment.approved_comment)

    def test_invalid_comment_is_not_saved(self):
        response = self.client.post(self.url, {'author': '', 'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)

    def test_missing_post_is_404(self):
        response = self.client.get(reverse('blog:add_comment_to_post', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_visitor_cannot_comment_on_draft(self):
        draft = make_post(self.user, published=False)
        url = reverse('blog:add_comment_to_post', args=[draft.pk])
        response = self.client.post(url, {'author': 'Ana', 'text': 'Hi'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)

    def test_logged_in_user_can_comment_on_draft(self):
        draft = make_post(self.user, published=False)
        self.client.force_login(self.user)
        url = reverse('blog:add_comment_to_post', args=[draft.pk])
        self.client.post(url, {'author': 'Me', 'text': 'Note'})
        self.assertEqual(draft.comments.count(), 1)


class CommentVisibilityTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user)
        self.url = reverse('blog:post_detail', args=[self.post.pk])

    def test_visitor_sees_approved_comment(self):
        make_comment(self.post, author='Ana', text='Approved text', approved=True)
        response = self.client.get(self.url)
        self.assertContains(response, 'Approved text')
        self.assertContains(response, 'Posted by: Ana')

    def test_visitor_does_not_see_unapproved_comment(self):
        make_comment(self.post, text='Waiting text', approved=False)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Waiting text')

    def test_logged_in_user_sees_unapproved_comment_with_actions(self):
        comment = make_comment(self.post, text='Waiting text', approved=False)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Waiting text')
        self.assertContains(response, reverse('blog:comment_approve', args=[comment.pk]))
        self.assertContains(response, reverse('blog:comment_remove', args=[comment.pk]))

    def test_approved_comment_has_no_moderation_actions(self):
        comment = make_comment(self.post, approved=True)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertNotContains(response, reverse('blog:comment_approve', args=[comment.pk]))

    def test_comment_html_is_escaped(self):
        make_comment(self.post, text='<script>alert(1)</script>', approved=True)
        response = self.client.get(self.url)
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_comment_author_is_escaped(self):
        make_comment(self.post, author='<img src=x onerror=alert(1)>', approved=True)
        response = self.client.get(self.url)
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')

    def test_no_comments_message(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'No comments')


class CommentApproveViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user)
        self.comment = make_comment(self.post)
        self.url = reverse('blog:comment_approve', args=[self.comment.pk])

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.approved_comment)

    def test_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_approves(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.pk]))
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.approved_comment)

    def test_missing_comment_is_404(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('blog:comment_approve', args=[999]))
        self.assertEqual(response.status_code, 404)


class CommentRemoveViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user)
        self.comment = make_comment(self.post)
        self.url = reverse('blog:comment_remove', args=[self.comment.pk])

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')
        self.assertTrue(Comment.objects.exists())

    def test_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Comment.objects.exists())

    def test_removes(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.pk]))
        self.assertFalse(Comment.objects.exists())

    def test_missing_comment_is_404(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('blog:comment_remove', args=[999]))
        self.assertEqual(response.status_code, 404)
