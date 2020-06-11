import random
from string import ascii_letters

from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post


User = get_user_model()


class TestPostsApp(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cooltester',
            email='corona_virus@china.com',
            password='SlavaKpss')
        self.post = {'text': 'Cool test text.'}
        self.test_urls = [reverse('index'),
                          reverse('profile', args=[self.user.username]),
                          ]
        self.test_user = User.objects.create_user(
            username='test',
            email='test@test.com',
            password='TestTest123')

    def test_profile(self):
        """"
        После регистрации пользователя создается его персональная страница (profile).
        """
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

    def test_guest(self):
        """Неавторизованный посетитель не может опубликовать пост 
        (его редиректит на страницу входа)."""
        response = self.client.post(
            reverse('new_post'), self.post, follow=False)
        login_url = reverse('login')
        new_url = reverse('new_post')
        self.assertRedirects(response, f'{login_url}?next={new_url}')

    def test_create_post(self):
        """Тест добавления поста через форму"""
        self.client.force_login(self.user)
        self.client.post(reverse('new_post'),
                         self.post, follow=True)
        post = Post.objects.order_by("-pub_date").first()
        self.assertEqual(self.post['text'], post.text)

    def test_new_post(self):
        self.post['author'] = self.user
        post = Post.objects.create(**self.post)
        for url in self.test_urls:
            response = self.client.get(url)
            self.assertIn(post, response.context['page'].object_list)
        response = self.client.get(
            reverse('post', args=[self.user.username, post.id]))
        self.assertEqual(response.context['post'], post)

        self.post['text'] = 'Now post editted'
        url = reverse('post_edit', args=[self.user.username, post.id])
        response = self.client.post(url, self.post, follow=True)
        for url in self.test_urls:
            response = self.client.get(url)
            self.assertIn(post, response.context['page'].object_list)
        response = self.client.get(
            reverse('post', args=[self.user.username, post.id]))
        self.assertEqual(response.context['post'], post)

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

    def test_img_all(self):
        self.client.force_login(self.user)
        self.post['author'] = self.user
        post = Post.objects.create(**self.post)
        edit_url = reverse('post_edit', args=[self.user.username, post.id])
        with open('posts/image.jpeg', 'rb') as img:
            self.client.post(edit_url, {'author': self.user,
                                        'text': 'It is rainning man',
                                        'image': img})

        self.test_urls.append(
            reverse('post', args=[self.user.username, post.id]))
        for url in self.test_urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertContains(response, '<img', status_code=200)

    def test_not_img(self):
        self.client.force_login(self.user)
        self.post['author'] = self.user
        with open('posts/wrong.txt', 'rb') as img:
            self.post['image'] = img
            response = self.client.post(reverse('new_post'),
                         self.post, follow=True)
        post = Post.objects.order_by("-pub_date").first()
        self.assertFalse(bool(post.image))

    def test_cache(self):
        pass

    def test_comment_auth_user(self):
        pass

    def test_comment_anon_user(self):
        anon_client = Client()
        self.client.force_login(self.user)
        self.post['author'] = self.user
        post = Post.objects.create(**self.post)
        login_url = reverse('login')
        comment_url = reverse('add_comment', args=[self.user.username, post.id])
        response = anon_client.post(comment_url, self.post, follow=False)
        self.assertRedirects(response, f'{login_url}?next={comment_url}')

    def test_follow(self):
        pass