from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user = User.objects.create_user(username='testuser')
        Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        Post.objects.create(
            author=cls.user,
            text='Тесовый пост где очень много текста.'
        )

    def setUp(self):
        # Гостевой клиент
        self.guest_client = Client()

        # Авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_url_exists_at_desired_location(self):
        """Проверка доступности адресов статических страниц."""
        unauthorized_url_pages = [
            '/',
            '/group/test_slug/',
            '/profile/testuser/',
            '/posts/1/'
        ]
        for url in unauthorized_url_pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_non_existent_pages(self):
        """Проверка отправки ошибки 404 несуществующих страниц."""
        unauthorized_url_pages = [
            '/group/not_existed_slug/',
            '/profile/not_existed_user/',
            '/posts/99999/',
            '/not_existed_page'
        ]
        for url in unauthorized_url_pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html'
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_edit_post_page_only_for_author(self):
        """Проверка отображения страницы для неавтора поста."""
        another_user = User.objects.create_user(username='another_testuser')
        another_authorized_client = Client()
        another_authorized_client.force_login(another_user)

        response = another_authorized_client.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/')

    def test_page_has_no_access_authorized_user(self):
        """Проверка отправки redirect для неавторизованных пользователей."""
        unauthorized_url_pages = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/'
        }
        for url, redirect_url in unauthorized_url_pages.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)
