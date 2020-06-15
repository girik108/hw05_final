import random
import time
from string import ascii_letters

from django.test import TestCase, Client, override_settings
from django.test.utils import setup_test_environment
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Comment, Follow


DUMMY_CACHE = {
    'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
}

User = get_user_model()


class TestPostsApp(TestCase):
    def setUp(self):
        # Клиент для анонимного пользователя.
        self.guest_client = Client()
        # Добавляем пользователя
        self.user = User.objects.create_user(
            username='cooltester',
            email='corona_virus@china.com',
            password='SlavaKpss')
        # Клиент для пользователя self.user.
        self.client = Client()
        # Логиним пользователя
        self.client.force_login(self.user)
        # Добавляем еще одного пользователя.
        self.other_user = User.objects.create_user(
            username='othertester',
            email='other@user.com',
            password='OtherUser123')
        self.other_client = Client()
        self.other_client.force_login(self.other_user)
        # Словарь значений для обьекта Post
        self.post_dict = {'text': 'Cool test text.', 'author': self.user}
        self.comment_dict = {'text': 'Hello world!', 'author': self.other_user}
        # Создаем обьект Post
        self.post = Post.objects.create(**self.post_dict)
        self.test_urls = [reverse('index'),  # /
                          # /username/
                          reverse('profile', args=[self.user.username]),
                          # /username/id
                          reverse('post', args=[
                                  self.user.username, self.post.id]),
                          ]

    def test_profile(self):
        """"
        После регистрации пользователя создается его персональная страница (profile).
        """
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

    def test_guest_create_post(self):
        """Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)."""
        response = self.guest_client.post(
            reverse('new_post'), self.post_dict, follow=False)
        login_url = reverse('login')
        new_url = reverse('new_post')
        self.assertRedirects(response, f'{login_url}?next={new_url}')

    def test_new_post_via_post(self):
        """Тест добавления поста через POST форму."""
        self.client.post(reverse('new_post'),
                         self.post_dict, follow=True)
        post = Post.objects.order_by("-pub_date").first()
        self.assertEqual(self.post_dict['text'], post.text)

    def test_new_post(self):
        for url in self.test_urls[:2]:
            response = self.guest_client.get(url)
            self.assertIn(self.post, response.context['page'].object_list)
        response = self.guest_client.get(self.test_urls[2])
        self.assertEqual(response.context['post'], self.post)
    
    @override_settings(CACHES=DUMMY_CACHE)
    def test_edit_post(self):
        self.post_dict['text'] = 'Now post editted'
        # URL /username/post_id/edit
        url = reverse('post_edit', args=[self.user.username, self.post.id])
        response = self.client.post(url, self.post_dict, follow=True)
        for url in self.test_urls[:2]:
            response = self.client.get(url)
            self.assertIn(self.post, response.context['page'].object_list)
        response = self.client.get(self.test_urls[2])
        self.assertEqual(response.context['post'], self.post)

    def test_HTTP404(self):
        test_int = random.randint(1000, 10000)
        test_str = ''.join(random.choice(ascii_letters) for i in range(12))
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('post', args=[self.user.username, test_int]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse('profile', args=[test_str]))
        self.assertEqual(response.status_code, 404)

    @override_settings(CACHES=DUMMY_CACHE)
    def test_img_all(self):
        edit_url = reverse('post_edit', args=[
                           self.user.username, self.post.id])
        with open('posts/image.jpeg', 'rb') as img:
            self.client.post(edit_url, {'author': self.user,
                                        'text': 'It is rainning man',
                                        'image': img})
        for url in self.test_urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertContains(response, '<img', status_code=200)

    def test_not_img(self):
        with open('posts/wrong.txt', 'rb') as img:
            self.post_dict['image'] = img
            response = self.client.post(reverse('new_post'),
                                        self.post_dict, follow=True)
        post = Post.objects.order_by('-pub_date').first()
        self.assertFalse(bool(post.image))

    def test_cache(self):
        # открываем список постов - видим пост
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.post.text, status_code=200)
        #обновляем пост
        self.post.text = 'New text, old post!'
        self.post.save()
        #открываем список постов - пост не изменился
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, self.post.text, status_code=200)
        time.sleep(21)
        #Ждем таймаут и проверяем, что теперь уже пост изменился.
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.post.text, status_code=200)


    def test_comment_auth_user(self):
        # URL Отправки комментария.
        comment_url = reverse('add_comment', args=[
                              self.user.username, self.post.id])
        # Отправка комментария
        response = self.other_client.post(comment_url,
                                          self.comment_dict,
                                          follow=True)
        # Страница с записью
        response = self.client.get(self.test_urls[2])
        # Проверка обьекта коментария в context
        comment = Comment.objects.get(post=self.post)
        self.assertIn(comment, response.context['comments'])

    def test_comment_anon_user(self):
        login_url = reverse('login')
        comment_url = reverse('add_comment', args=[
                              self.user.username, self.post.id])
        response = self.guest_client.post(comment_url,
                                          self.comment_dict,
                                          follow=False)
        self.assertRedirects(response, f'{login_url}?next={comment_url}')

    def test_follow(self):
        # Подписываемся на пользователя
        response = self.other_client.get(
            reverse('profile_follow', args=[self.user.username]))
        # Добавляем пост
        post = Post.objects.create(text='Post for followers', author=self.user)
        posts = (self.post, post)
        # Проверяем ленту
        response = self.other_client.get(reverse('follow_index'))
        for item in posts:
            with self.subTest():
                self.assertIn(item, response.context['page'].object_list)
        # Отписываемся от пользователя
        response = self.other_client.get(
            reverse('profile_unfollow', args=[self.user.username]))
        # проверяем ленту.
        response = self.other_client.get(reverse('follow_index'))
        for item in posts:
            with self.subTest():
                self.assertNotIn(item, response.context['page'].object_list)
