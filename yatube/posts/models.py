from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
TEST_EXAMPLE_STR = 15


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name="Название группы")
    slug = models.SlugField(max_length=50,
                            unique=True,
                            verbose_name="Ссылка группы")
    description = models.TextField(verbose_name="Описание группы")

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст поста")
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name="Дата публикации")
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name="Автор")
    group = models.ForeignKey(Group,
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name="Группа"
                              )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:TEST_EXAMPLE_STR]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name="Пост"
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name="Автор"
                               )
    text = models.TextField(verbose_name="Текст комментария")
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name="Дата публикации"
                                   )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return self.text[:TEST_EXAMPLE_STR]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Автор'
                               )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique appversion')
        ]
