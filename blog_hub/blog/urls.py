from django.urls import path
from .views import post_views,static_views

app_name = 'blog'

urlpatterns = [
    path('', post_views.PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', post_views.PostDetailView.as_view(), name='post_detail'),  
    path('post/new/', post_views.PostCreateView.as_view(), name='post_new'), 
    path('post/<int:pk>/edit', post_views.PostUpdateView.as_view(), name='post_edit'),

    path('about/', static_views.AboutView.as_view(), name='about'),

]