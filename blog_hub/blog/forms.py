from django import forms
from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        # The author is always the logged-in user, set in the view
        fields = ('title','text')

        widgets = {
            'title' : forms.TextInput(attrs = {'class':'text-input-class'}),
            'text' : forms.Textarea(attrs = {'class':'editable medium-editor-textarea post-content'}),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('author','text')

        # Comments come from anonymous visitors, so they are plain text (no rich editor, no HTML)
        widgets = {
            'author' : forms.TextInput(attrs = {'class':'text-input-class'}),
            'text' : forms.Textarea(attrs = {'class':'form-control comment-textarea', 'rows': 5}),
        }
