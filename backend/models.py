from django.db import models


class BusinessRequest(models.Model):
    title = models.CharField(
        "Название",
        max_length=200,
    )

    description = models.TextField(
        "Описание",
        max_length=5000,
    )

    need = models.TextField(
        "Потребность",
        max_length=5000,
        blank=True,
        default="",
    )

    expected_result = models.TextField(
        "Ожидаемый результат",
        max_length=2000,
        blank=True,
    )

    contact = models.CharField(
        "Контакт",
        max_length=255,
        blank=True,
        default="",
    )

    interaction_format = models.CharField(
        "Формат взаимодействия",
        max_length=255,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    # Старые поля сохраняем, чтобы не удалять данные прежних заявок.
    # В новой пользовательской форме они не отображаются.
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

    email = models.EmailField(
        "Email для связи",
        blank=True,
    )

    request_type = models.CharField(
        "Тип обращения",
        max_length=10,
        choices=REQUEST_TYPES,
        blank=True,
    )

    class Meta:
        verbose_name = "Заявка бизнеса"
        verbose_name_plural = "Заявки бизнеса"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title