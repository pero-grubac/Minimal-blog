from django.test import TestCase

from blog.forms import CommentForm, PostForm


class PostFormTests(TestCase):
    def test_valid_with_title_and_text(self):
        form = PostForm(data={'title': 'Title', 'text': 'Body'})
        self.assertTrue(form.is_valid())

    def test_author_is_not_a_form_field(self):
        # The author comes from the logged-in user, never from the request body
        self.assertNotIn('author', PostForm().fields)

    def test_title_is_required(self):
        form = PostForm(data={'title': '', 'text': 'Body'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_text_is_required(self):
        form = PostForm(data={'title': 'Title', 'text': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_title_max_length(self):
        form = PostForm(data={'title': 'x' * 201, 'text': 'Body'})
        self.assertFalse(form.is_valid())

    def test_text_uses_medium_editor(self):
        css = PostForm().fields['text'].widget.attrs['class']
        self.assertIn('editable', css)


class CommentFormTests(TestCase):
    def test_valid_with_author_and_text(self):
        form = CommentForm(data={'author': 'Ana', 'text': 'Hi'})
        self.assertTrue(form.is_valid())

    def test_fields(self):
        self.assertEqual(list(CommentForm().fields), ['author', 'text'])

    def test_author_is_required(self):
        form = CommentForm(data={'author': '', 'text': 'Hi'})
        self.assertFalse(form.is_valid())

    def test_text_is_required(self):
        form = CommentForm(data={'author': 'Ana', 'text': ''})
        self.assertFalse(form.is_valid())

    def test_text_is_plain_textarea(self):
        # Comments are untrusted, so they must not get the rich-text editor
        css = CommentForm().fields['text'].widget.attrs['class']
        self.assertNotIn('editable', css)
