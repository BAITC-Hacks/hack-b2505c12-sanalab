from django.db import models
from django.utils import timezone


class BusinessRequest(models.Model):
    """Заявка: свободный ввод, редактирование и явное подтверждение автором."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        CONFIRMED = "confirmed", "Подтверждена"

    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", max_length=5000)
    need = models.TextField(
        "Потребность", max_length=5000, blank=True, default="",
    )
    expected_result = models.TextField(
        "Ожидаемый результат", max_length=2000, blank=True,
    )
    contact = models.CharField(
        "Контакт", max_length=255, blank=True, default="",
    )
    interaction_format = models.CharField(
        "Формат взаимодействия", max_length=255, blank=True, default="",
    )

    status = models.CharField(
        "Статус", max_length=16, choices=Status.choices,
        default=Status.DRAFT, editable=False,
    )
    confirmed_at = models.DateTimeField(
        "Дата подтверждения", null=True, blank=True, editable=False,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField(
        "Дата изменения", default=timezone.now, editable=False,
    )
    revision = models.PositiveIntegerField(
        "Версия карточки", default=1, editable=False,
    )
    # Не даём просматривать чужие контакты или править чужие заявки по номеру.
    # Пустой ключ остаётся у старых записей; сайт их никому не присваивает.
    owner_key = models.CharField(
        "Ключ сессии автора", max_length=64, blank=True,
        default="", editable=False, db_index=True,
    )

    # Старые поля не удаляем: данные прежних заявок сохраняются.
    # В новой форме они не используются.
    REQUEST_TYPES = [
        ("need", "Потребность"),
        ("problem", "Проблема"),
        ("task", "Задача"),
    ]
    company = models.CharField("Компания", max_length=150, blank=True)
    email = models.EmailField("Email для связи", blank=True)
    request_type = models.CharField(
        "Тип обращения", max_length=10, choices=REQUEST_TYPES, blank=True,
    )

    class Meta:
        verbose_name = "Заявка бизнеса"
        verbose_name_plural = "Заявки бизнеса"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title
