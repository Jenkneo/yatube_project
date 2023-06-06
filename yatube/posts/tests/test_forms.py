from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment
# from posts.forms import PostForm, CommentForm

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=f'Тесовый пост автора {cls.user.username} принадлежащий '
                 f'группе {cls.group.title} где очень много текста.',
            group=cls.group
        )
        # cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_image = SimpleUploadedFile(
            name='image1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.pk,
            'image': uploaded_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        post = Post.objects.filter(
            text='Тестовая запись',
            group=self.group,
            image='posts/image1.gif'
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(post.exists())
        post.delete()

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_image = SimpleUploadedFile(
            name='image2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Пост без картинки',
            group=self.group
        )
        new_text = 'Пост с картинкой'
        form_data = {
            'text': new_text,
            'image': uploaded_image,
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post.pk]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                text=new_text,
                image='posts/image2.gif',
                group=self.group
            ).exists()
        )
        post.delete()

    def test_cant_create_post_no_authorized_user(self):
        """Гость не может создавать посты"""
        guest_client = Client()
        post_count = Post.objects.count()
        post_text = 'Тесовый пост который создает гость'
        form_data = {
            'text': post_text,
            'group': '',
        }
        guest_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_cant_edit_post_no_authorized_user(self):
        """Гость не может редактировать посты"""
        old_text = self.post.text
        guest_client = Client()
        post_text = 'Тесовый пост который редактирует гость'
        form_data = {
            'text': post_text
        }
        guest_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, old_text)

    def test_cant_edit_post_another_authorized_user(self):
        """Пользователь не может редактировать посты другого автора"""
        old_text = self.post.text
        anotheruser = User.objects.create_user(username='anotheruser')
        another_authorized_client = Client()
        another_authorized_client.force_login(anotheruser)
        post_text = 'Тесовый пост который редактирует другой пользователь'
        form_data = {
            'text': post_text
        }
        another_authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, old_text)

    def test_create_comment_to_post(self):
        """Авторизированный пользователь может оставлять комментарии"""
        comments_count = Comment.objects.filter(post=self.post).count()
        comment_text = 'Тестовый комментарий'
        form_data = {
            'text': comment_text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.filter(post=self.post).count(),
                         comments_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Comment.objects.filter(
                text=comment_text,
                author=self.user
            ).exists())

    def test_guest_user_cant_create_comment_to_post(self):
        """Не авторизированный пользователь может оставлять комментарии"""
        comments_count = Comment.objects.filter(post=self.post).count()
        form_data = {'text': 'Тестовый комментарий'}
        Client().post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.filter(post=self.post).count(),
                         comments_count)
