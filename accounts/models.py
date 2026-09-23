from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    class Role(models.TextChoices):
        BUSINESS = "business", "Представитель бизнеса"
        STUDENT = "student", "Студент"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_profile",
    )
    role = models.CharField(max_length=10, choices=Role.choices)

    def __str__(self):
        return f"{self.user.username}: {self.get_role_display()}"