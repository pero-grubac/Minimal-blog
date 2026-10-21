from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from blog.models import Comment
from blog.forms import CommentForm
from blog.views.post_views import visible_posts


# Anyone can comment; the comment stays hidden until a logged-in user approves it
def add_comment_to_post(request,pk):
    post = get_object_or_404(visible_posts(request.user),pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()

            return redirect('blog:post_detail',pk=post.pk)

    else:
        form = CommentForm()

    return render(request,'blog/comment/comment_form.html',{'form':form, 'post':post})

@login_required
@require_POST
def comment_approve(request,pk):
    comment = get_object_or_404(Comment,pk=pk)
    comment.approve()
    return redirect('blog:post_detail',pk=comment.post.pk)


@login_required
@require_POST
def comment_remove(request,pk):
    comment = get_object_or_404(Comment,pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('blog:post_detail',pk=post_pk)
