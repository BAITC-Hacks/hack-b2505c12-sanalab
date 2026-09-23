from django import forms
from backend.models import BusinessRequest


class BusinessRequestForm(forms.ModelForm):
    class Meta:
        model = BusinessRequest

        fields = [
            "company",
            "email",
            "request_type",
            "title",
            "description",
            "expected_result",
        ]

        widgets = {
            "company": forms.TextInput(attrs={
                "placeholder": "Название компании",
                "autocomplete": "organization",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }),
            "title": forms.TextInput(attrs={
                "placeholder": "Например, автоматизация записи клиентов",
            }),
            "description": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Опишите ситуацию и что нужно изменить…",
            }),
            "expected_result": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Какой результат вы хотите получить?",
            }),
        }

        help_texts = {
            "description": "До 5000 символов.",
            "expected_result": "До 2000 символов.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.error_messages["required"] = "Заполните это поле."
            field.error_messages["max_length"] = (
                "Слишком длинный текст. Максимум — %(limit_value)s символов."
            )

        self.fields["email"].error_messages["invalid"] = (
            "Введите корректный email."
        )
        self.fields["request_type"].error_messages["invalid_choice"] = (
            "Выберите вариант из списка."
        )