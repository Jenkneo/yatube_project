from django import forms
from .models import Post, Comment
from django.utils.translation import gettext_lazy as _


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': _('Текст записи'),
                  'group': _('Группа'),
                  'image': _('Изображение')
                  }
        help_texts = {
            'text': _('Текст поста'),
            'group': _('Группа, к которой будет относиться пост'),
            'image': _('Изображение поста')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
        help_texts = {'text': _('Текст комментария'), }
