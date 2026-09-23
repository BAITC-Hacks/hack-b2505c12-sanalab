from django import forms
from backend.models import BusinessRequest


class BusinessRequestForm(forms.ModelForm):
    class Meta:
        model = BusinessRequest

        fields = [
            "title",
            "description",
            "need",
            "expected_result",
            "contact",
            "interaction_format",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # В новой заявке обязательны все шесть полей.
        for field in self.fields.values():
            field.required = True

            field.error_messages["required"] = (
                "Заполните это поле."
            )

            field.error_messages["max_length"] = (
                "Слишком длинный текст. "
                "Максимум — %(limit_value)s символов."
            )