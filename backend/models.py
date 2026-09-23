from django.db import models


class BusinessRequest(models.Model):
    REQUEST_TYPES = [
        ("need", "Потребность"),
        ("problem", "Проблема"),
        ("task", "Задача"),
    ]

    company = models.CharField(
        "Компания",
        max_length=150,
        blank=True,
    )
    email = models.EmailField("Email для связи")
    request_type = models.CharField(
        "Тип обращения",
        max_length=10,
        choices=REQUEST_TYPES,
    )
    title = models.CharField(
        "Краткое название",
        max_length=200,
    )
    description = models.TextField(
        "Описание",
        max_length=5000,
    )
    expected_result = models.TextField(
        "Ожидаемый результат",
        max_length=2000,
        blank=True,
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Заявка бизнеса"
        verbose_name_plural = "Заявки бизнеса"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title