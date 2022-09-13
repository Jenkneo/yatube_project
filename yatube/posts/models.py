from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your models here.
class Post(models.Model):
    text = models.TextField()

    # параметр auto_now_add определяет, что в поле будет автоматически
    # подставлено время и дата создания новой записи
    pub_date = models.DateTimeField(auto_now_add=True)

    # Тип: ForeignKey, ссылка на модель User
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts')
