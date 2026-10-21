from django.test import TestCase
from django.urls import reverse

from blog.tests.factories import make_user


class AboutPageTests(TestCase):
    def test_renders(self):
        response = self.client.get(reverse('blog:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/util/about.html')
        self.assertContains(response, 'About this project')


class LayoutTests(TestCase):
    def test_visitor_sees_login_link(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, reverse('login'))
        self.assertNotContains(response, reverse('blog:post_new'))

    def test_logged_in_user_sees_writer_links(self):
        user = make_user('pero')
        self.client.force_login(user)
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, reverse('blog:post_new'))
        self.assertContains(response, reverse('blog:draft_list'))
        self.assertContains(response, 'Welcome: pero')

    def test_stylesheet_is_linked(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, 'css/blog.css')


class AuthTests(TestCase):
    def setUp(self):
        self.user = make_user('pero', 'secret-pass-123')

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertContains(response, 'Please Login')

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse('login'), {'username': 'pero', 'password': 'secret-pass-123'}
        )
        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse('login'), {'username': 'pero', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wrong credentials')

    def test_login_redirects_to_next(self):
        next_url = reverse('blog:draft_list')
        response = self.client.post(
            reverse('login'),
            {'username': 'pero', 'password': 'secret-pass-123', 'next': next_url},
        )
        self.assertRedirects(response, next_url)

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)


class AdminTests(TestCase):
    def test_models_are_registered(self):
        admin = make_user('admin')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.client.force_login(admin)

        response = self.client.get(reverse('admin:index'))

        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Comments')
