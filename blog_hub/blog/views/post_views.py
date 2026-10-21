from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy,reverse
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView, DetailView, CreateView,
    UpdateView, DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from blog.models import Post
from blog.forms import PostForm


def visible_posts(user):
    """Logged-in users see drafts too, visitors only published posts."""
    if user.is_authenticated:
        return Post.objects.all()
    return Post.objects.filter(published_date__lte=timezone.now())


class PostListView(ListView):
    model = Post
    template_name = 'blog/post/post_list.html'

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post/post_detail.html'

    def get_queryset(self):
        return visible_posts(self.request.user)

class PostCreateView(LoginRequiredMixin,CreateView):
    form_class = PostForm
    model = Post
    template_name = 'blog/post/post_form.html'
    success_url = reverse_lazy('blog:draft_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin,UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'blog/post/post_form.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk})

class PostDeleteView(LoginRequiredMixin,DeleteView):
    model = Post
    template_name = 'blog/post/post_delete.html'
    success_url = reverse_lazy('blog:post_list')


class DraftListView(LoginRequiredMixin,ListView):
    model = Post
    template_name = 'blog/post/post_draft_list.html'

    def get_queryset(self):
        return Post.objects.filter(published_date__isnull=True).order_by('-create_date')


@login_required
@require_POST
def post_publish(request,pk):
    post = get_object_or_404(Post,pk=pk)
    post.publish()
    return redirect('blog:post_detail',pk=pk)
