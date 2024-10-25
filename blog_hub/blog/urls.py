from django.urls import path
from .views import post_views,static_views,comment_views

app_name = 'blog'

urlpatterns = [
    path('', post_views.PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', post_views.PostDetailView.as_view(), name='post_detail'),  
    path('post/new/', post_views.PostCreateView.as_view(), name='post_new'), 
    path('post/<int:pk>/edit/', post_views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<int:pk>/remove/', post_views.PostDeleteView.as_view(), name='post_remove'),
    path('post/<int:pk>/publish/', post_views.post_publish, name='post_publish'),

    path('drafts/', post_views.DraftListView.as_view(), name='draft_list'),

    path('post/<int:pk>/comment/', comment_views.add_comment_to_post, name='add_comment_to_post'),
    path('comment/<int:pk>/approve', comment_views.comment_approve, name='comment_approve'),
    path('comment/<int:pk>/remove', comment_views.comment_remove, name='comment_remove'),


    path('about/', static_views.AboutView.as_view(), name='about'),

]