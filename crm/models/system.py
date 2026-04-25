from django.db import models

class QuickReply(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название шаблона")
    text = models.TextField(verbose_name="Текст ответа")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Быстрый ответ"
        verbose_name_plural = "Быстрые ответы"
        ordering = ['title']

    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.title}"
