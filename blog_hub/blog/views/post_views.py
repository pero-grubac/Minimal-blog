from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
)
from .models import Post
from .forms import PostForm
from django.contrib.auth.mixins import LoginRequiredMixin

class PostListView(ListView):
    model = Post
    
    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now().order_by('-published_date'))

class PostDetailView(DetailView):
    model = Post
    
class PostCreateView(LoginRequiredMixin,CreateView):
    login_url = '/login'
    redirect_field_name = 'next'
    form_class = PostForm
    model = Post
    template_name = 'blog/post/post_form.html'
    # TODO switch to drafts
    success_url = reverse_lazy('blog:post_list')  

class PostUpdateView(LoginRequiredMixin,UpdateView):
    login_url = '/login'
    redirect_field_name = 'next'
    form_class = PostForm
    model = Post
    template_name = 'blog/post/post_form.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk})

