from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        'date published', auto_now_add=True, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey('Group', on_delete=models.SET_NULL,
                              blank=True, null=True, related_name='posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ['-pub_date']


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.title} - {self.slug}'


class Comment(models.Model):
    text = models.TextField()
    created = models.DateTimeField(verbose_name='date created ',
                                   auto_now_add=True)
    post = models.ForeignKey('Post', on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    #  ссылка на объект пользователя, который подписывается.
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    # ссылка на объект пользователя, на которого подписываются.
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')
