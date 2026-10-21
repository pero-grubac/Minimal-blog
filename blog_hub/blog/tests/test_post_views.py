from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post
from blog.tests.factories import make_post, make_user

LOGIN_URL = reverse('login')


class PostListViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_shows_published_posts(self):
        make_post(self.user, title='Published one')
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/post_list.html')
        self.assertContains(response, 'Published one')

    def test_hides_drafts(self):
        make_post(self.user, title='Secret draft', published=False)
        response = self.client.get(reverse('blog:post_list'))
        self.assertNotContains(response, 'Secret draft')

    def test_hides_posts_scheduled_in_the_future(self):
        make_post(self.user, title='Future post', published=False)
        Post.objects.update(published_date=timezone.now() + timedelta(days=1))
        response = self.client.get(reverse('blog:post_list'))
        self.assertNotContains(response, 'Future post')

    def test_newest_first(self):
        older = make_post(self.user, title='Older')
        newer = make_post(self.user, title='Newer')
        Post.objects.filter(pk=older.pk).update(published_date=timezone.now() - timedelta(days=2))
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(list(response.context['post_list']), [newer, older])

    def test_empty_message(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, 'No published posts available.')

    def test_counts_only_approved_comments(self):
        post = make_post(self.user)
        post.comments.create(author='a', text='x', approved_comment=True)
        post.comments.create(author='b', text='y', approved_comment=False)
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, 'Comments: 1')


class PostDetailViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_published_post_is_public(self):
        post = make_post(self.user, title='Hello', text='World')
        response = self.client.get(reverse('blog:post_detail', args=[post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello')
        self.assertContains(response, 'World')

    def test_draft_is_hidden_from_visitors(self):
        post = make_post(self.user, published=False)
        response = self.client.get(reverse('blog:post_detail', args=[post.pk]))
        self.assertEqual(response.status_code, 404)

    def test_draft_is_visible_when_logged_in(self):
        post = make_post(self.user, title='My draft', published=False)
        self.client.force_login(self.user)
        response = self.client.get(reverse('blog:post_detail', args=[post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Publish')

    def test_missing_post_is_404(self):
        response = self.client.get(reverse('blog:post_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_visitors_do_not_see_edit_controls(self):
        post = make_post(self.user)
        response = self.client.get(reverse('blog:post_detail', args=[post.pk]))
        self.assertNotContains(response, reverse('blog:post_edit', args=[post.pk]))
        self.assertNotContains(response, reverse('blog:post_remove', args=[post.pk]))

    def test_logged_in_user_sees_edit_controls(self):
        post = make_post(self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse('blog:post_detail', args=[post.pk]))
        self.assertContains(response, reverse('blog:post_edit', args=[post.pk]))
        self.assertContains(response, reverse('blog:post_remove', args=[post.pk]))


class PostCreateViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('blog:post_new')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')

    def test_form_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Post')

    def test_creates_draft_owned_by_current_user(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': 'Fresh', 'text': 'Body'})

        self.assertRedirects(response, reverse('blog:draft_list'))
        post = Post.objects.get()
        self.assertEqual(post.author, self.user)
        self.assertIsNone(post.published_date)

    def test_cannot_post_as_another_author(self):
        other = make_user('other')
        self.client.force_login(self.user)
        self.client.post(self.url, {'title': 'T', 'text': 'B', 'author': other.pk})
        self.assertEqual(Post.objects.get().author, self.user)

    def test_invalid_form_shows_errors(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': '', 'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)


class PostUpdateViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user, title='Old title')
        self.url = reverse('blog:post_edit', args=[self.post.pk])

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')

    def test_form_says_edit(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Edit Post')
        self.assertContains(response, 'Old title')

    def test_updates_and_redirects_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': 'New title', 'text': 'New body'})

        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.pk]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'New title')
        self.assertEqual(self.post.author, self.user)

    def test_missing_post_is_404(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('blog:post_edit', args=[999]))
        self.assertEqual(response.status_code, 404)


class PostDeleteViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user, title='To delete')
        self.url = reverse('blog:post_remove', args=[self.post.pk])

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')
        self.assertTrue(Post.objects.exists())

    def test_get_asks_for_confirmation(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'Are you sure you want to delete To delete')
        self.assertTrue(Post.objects.exists())

    def test_post_deletes(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('blog:post_list'))
        self.assertFalse(Post.objects.exists())


class DraftListViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('blog:draft_list')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')

    def test_lists_only_drafts(self):
        make_post(self.user, title='Draft one', published=False)
        make_post(self.user, title='Live one')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, 'Draft one')
        self.assertNotContains(response, 'Live one')

    def test_preview_strips_html(self):
        make_post(self.user, text='<b>bold</b> words', published=False)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'bold words')
        self.assertNotContains(response, '<b>bold</b>')

    def test_empty_message(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'No drafts available.')


class PostPublishViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.post = make_post(self.user, published=False)
        self.url = reverse('blog:post_publish', args=[self.post.pk])

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f'{LOGIN_URL}?next={self.url}')
        self.post.refresh_from_db()
        self.assertIsNone(self.post.published_date)

    def test_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.post.refresh_from_db()
        self.assertIsNone(self.post.published_date)

    def test_publishes(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.pk]))
        self.post.refresh_from_db()
        self.assertIsNotNone(self.post.published_date)

    def test_published_post_appears_on_home(self):
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.client.logout()
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, self.post.title)

    def test_missing_post_is_404(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('blog:post_publish', args=[999]))
        self.assertEqual(response.status_code, 404)
