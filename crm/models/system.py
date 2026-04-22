from django.db import models

class QuickReply(models.fields.Model):
    title = models.CharField(max_length=100, verbose_name="Название (для вас)")
    message_text = models.TextField(verbose_name="Текст сообщения для клиента")

    class Meta:
        verbose_name = "Быстрый ответ"
        verbose_name_plural = "4. Быстрые ответы (Шаблоны)"

    def __str__(self):
        return self.title
