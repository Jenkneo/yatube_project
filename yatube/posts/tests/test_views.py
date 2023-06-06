from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from http import HTTPStatus

from posts.views import POST_ON_PAGE
from posts.models import Group, Post, Comment, Follow

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user1 = User.objects.create_user(username='testuser1')
        cls.user2 = User.objects.create_user(username='testuser2')

        group_list = []
        for num in [1, 2]:
            group_list.append(
                Group.objects.create(
                    title=f'Тестовая группа {num}',
                    slug=f'test_slug{num}',
                    description=f'Тестовое описание группы {num}'
                )
            )
        cls.group1 = group_list[0]
        cls.group2 = group_list[1]

        temp_data = []
        for num in range(1, 40 + 1):
            # Все посты с id кратному 2 прнадлежат user2 и группе2
            if num % 2 != 0:
                author = cls.user1
                group = cls.group1
            else:
                author = cls.user2
                group = cls.group2

            temp_data.append(Post(
                author=author,
                text=f'Тесовый пост автора {author.username} принадлежащий '
                     f'группе {group.title} где очень много текста.',
                group=group
            ))
        Post.objects.bulk_create(temp_data, batch_size=99)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test_slug1'}),
            'posts/profile.html': reverse('posts:profile', args=['testuser1']),
            'posts/post_detail.html': reverse('posts:post_detail', args=['1']),
            'posts/create_post.html': reverse('posts:post_create')
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.authorized_client.get(
            reverse('posts:post_edit', args=['1'])
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_context_group_in_group_list_page(self):
        """view-функция передает верные посты группы."""
        url = reverse('posts:group_list', kwargs={'slug': self.group1.slug})
        response = self.guest_client.get(url)

        for post in response.context['page_obj'].object_list:
            with self.subTest(url=url):
                self.assertEqual(post.group.slug, self.group1.slug)

    def test_context_author_in_profile_page(self):
        """view-функция передает верные посты автора."""
        url = reverse('posts:profile', args=['testuser1'])
        response = self.guest_client.get(url)

        for post in response.context['page_obj'].object_list:
            with self.subTest(url=url):
                self.assertEqual(post.author.get_username(), 'testuser1')

    def test_context_image_in_posts_output_page(self):
        """Страница выводит изображения постов."""
        post = Post.objects.create(
            author=self.user1,
            text='Тесовый пост с картинкой',
            image=self.uploaded_image,
            group=self.group1
        )
        pages = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user1.username}),
            reverse('posts:group_list', kwargs={'slug': self.group1.slug}),
        ]

        for page in pages:
            with self.subTest(msg='Пост не попал на необходимые страницы',
                              reverse=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.context['page_obj'].object_list[0].image,
                    post.image
                )

    def test_context_image_in_post_detail_page(self):
        """Страница post_detail выводит изображене поста."""
        post = Post.objects.create(
            author=self.user1,
            text='Тесовый пост с картинкой',
            image=self.uploaded_image,
            group=self.group1
        )
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(
            response.context['post'].image,
            post.image
        )
        post.delete()

    def test_context_post_in_post_detail_page(self):
        """view-функция передает запрошенный пост."""
        post_id = 1
        url = reverse('posts:post_detail', kwargs={'post_id': post_id})
        response = self.guest_client.get(url)
        self.assertEqual(response.context['post'].pk, post_id)

    def test_post_create_and_edit_page_show_correct_form(self):
        """view-функция верно сформировала форму"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        pages_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=['1'])
        ]
        responses = []
        for page in pages_list:
            responses.append(self.authorized_client.get(page))

        for response in responses:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """view-функция верно передала данные в форму"""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      args=['1']))
        correct_data = Post.objects.get(pk=1)
        self.assertEqual(response.context['post'].text, correct_data.text)
        self.assertEqual(response.context['post'].group, correct_data.group)

    def test_created_post_show_correct_in_pages(self):
        """
        Проверка поста на отображение на необходимых страницах
        """
        cache.clear()
        user = self.user1
        group = self.group1
        correct_data = 'Проверка поста на отображение на необходимых страницах'
        post = Post.objects.create(
            author=user,
            text=correct_data,
            group=group,
            image=self.uploaded_image
        )
        reverse_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group1.slug}),
            reverse('posts:profile', kwargs={'username': self.user1.username})
        ]
        for reverse_obj in reverse_list:
            with self.subTest(msg='Пост не попал на необходимые страницы',
                              reverse=reverse_obj):
                response = self.guest_client.get(reverse_obj)
                page_data = response.context['page_obj'].object_list[0].text
                self.assertEqual(page_data, correct_data)

        for reverse_obj in reverse_list:
            with self.subTest(msg='Страница не отображает изобржения',
                              reverse=reverse_obj):
                response = self.Client().get(reverse_obj)
                page_image = response.context['page_obg'].object_list[0].image
                self.assertEqual(page_image, self.uploaded_image)

        with self.subTest(msg='Созданный пост попадает в другие группы'):
            incorrect_group = reverse('posts:group_list',
                                      kwargs={'slug': 'test_slug2'})
            response = self.guest_client.get(incorrect_group)
            page_data = response.context['page_obj'].object_list[0].text
            self.assertNotEqual(page_data, correct_data)

        post.delete()

    def test_created_post_show_correct_in_pages(self):
        """
        Проверка отображения комментария
        """
        comment_text = 'Тестовый комментарий'
        comment_author = self.user1
        comment_post = Post.objects.get(id=1)
        Comment.objects.create(
            text=comment_text,
            author=comment_author,
            post=comment_post
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': comment_post.id})
        )
        comment = response.context['post'].comments.get(text=comment_text)
        self.assertEqual(comment.text, comment_text)
        self.assertEqual(comment.author, comment_author)
        self.assertEqual(comment.post, comment_post)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PaginatorTestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )

        temp_data = []
        for num in range(1, 40 + 1):
            temp_data.append(Post(
                author=cls.user,
                text='Тесовый пост',
                group=cls.group
            ))
        Post.objects.bulk_create(temp_data, batch_size=99)

    def test_paginator_page_in_post_output_pages(self):
        """URL-адрес использует первую страницу Paginator."""
        pages = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        ]
        for url in pages:
            with self.subTest(url=url):
                response = Client().get(url)
                self.assertEqual(
                    response.context['page_obj'].number,
                    response.context['page_obj'].paginator.page(1).number
                )

    def test_paginator_context_posts_in_post_output_pages(self):
        """URL-адрес использует 10 постов на странице."""
        pages = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        ]
        for url in pages:
            with self.subTest(url=url):
                response = Client().get(url)
                self.assertEqual(
                    len(response.context['page_obj'].object_list), POST_ON_PAGE
                )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='pushkin')
        cls.user2 = User.objects.create_user(username='mayakovski')

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user1)
        self.follower = Client()
        self.follower.force_login(self.user2)

    def test_follow(self):
        """Проверка подписки и отписки на автора"""
        self.follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user1.username}
            )
        )
        with self.subTest(msg='Пользователь не может подписаться на автора.'):
            self.assertTrue(
                Follow.objects.filter(
                    author=self.user1.id,
                    user=self.user2.id
                ).exists()
            )
        self.follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user1.username}
            )
        )
        with self.subTest(msg='Пользователь не может отписаться от автора.'):
            self.assertFalse(
                Follow.objects.filter(
                    author=self.user1.id,
                    user=self.user2.id
                ).exists()
            )

    def test_follow_display_post(self):
        """Проверка отображения поста в follow_index"""
        Follow.objects.create(
            user=self.user2,
            author=self.user1
        )
        post_text = 'Тестовый пост для отображения в подписках'
        Post.objects.create(
            text=post_text,
            author=self.user1
        )
        response = self.follower.get(reverse('posts:follow_index'))
        with self.subTest(msg='Новый пост не появился в подписках.'):
            self.assertTrue(
                response.context['page_obj'].object_list[0].text,
                post_text
            )

        response = Client().get(reverse('posts:follow_index'))
        with self.subTest(
                msg='Гостевой пользователь заходит на страницу подписок'
        ):
            self.assertRedirects(
                response,
                '/auth/login/?next=/follow/'
            )

        response = self.author.get(reverse('posts:follow_index'))
        with self.subTest(msg='Новая запись появилась не там где нужно'):
            self.assertEqual(
                len(response.context['page_obj'].object_list),
                0
            )


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='CacheTestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тесты на проверку кеша'
        )

    def test_cache_index_page(self):
        """Тест проверки работоспособности кеша"""
        cache.clear()
        post_text = self.post.text
        page_before = Client().get(reverse('posts:index')).content.decode()
        self.post.text = 'Измененный текст'
        self.post.save()
        page_after = Client().get(reverse('posts:index')).content.decode()
        cache.clear()
        page_with_new_text = Client().get(
            reverse('posts:index')
        ).content.decode()
        self.assertIn(post_text, page_before)
        self.assertIn(post_text, page_after)
        self.assertNotIn(post_text, page_with_new_text)


class CustomTemplatesError(TestCase):
    def test404template(self):
        """Тест проверки использования кастомного шаблона 404"""
        response = Client().get('non_existed_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
