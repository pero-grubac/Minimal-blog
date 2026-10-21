from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from blog.models import Comment, Post


def make_user(username='writer', password='secret-pass-123'):
    return User.objects.create_user(username=username, password=password)


def make_post(author, title='A post', text='Some text', published=True, **kwargs):
    published_date = timezone.now() - timedelta(minutes=1) if published else None
    return Post.objects.create(
        author=author, title=title, text=text, published_date=published_date, **kwargs
    )


def make_comment(post, author='Visitor', text='Nice post', approved=False):
    return Comment.objects.create(
        post=post, author=author, text=text, approved_comment=approved
    )
