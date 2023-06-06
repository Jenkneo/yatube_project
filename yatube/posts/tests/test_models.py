from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Post, Group


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тесовый пост где очень много текста.'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        models_list = {
            'Тесовый пост гд': self.post,
            'Тестовая группа': self.group
        }
        for field, testing_model in models_list.items():
            with self.subTest(field=field):
                self.assertEqual(str(testing_model), field)
