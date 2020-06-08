from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Главная страница
    path('new/', views.new_post, name='new_post'),  # Новая запись
    path('<str:username>/', views.profile, name='profile'),  # Профайл пользователя
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),  # Просмотр записи
    path('<str:username>/<int:post_id>/edit/', views.post_edit, name='post_edit'),  
    path('<str:username>/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('group/<slug:slug>/', views.group_posts, name='group'),
]