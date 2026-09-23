from django import forms

from backend.models import BusinessRequest


class BusinessRequestForm(forms.ModelForm):
    class Meta:
        model = BusinessRequest
        # Только данные заявки. Статус и принадлежность задаёт сервер.
        fields = [
            "title", "description", "need", "expected_result",
            "contact", "interaction_format",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Например, автоматизация записи клиентов",
            }),
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Как устроен процесс сейчас? Какие сложности возникают?",
            }),
            "need": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Какой инструмент, услуга или помощь вам необходимы?",
            }),
            "expected_result": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Что должно измениться? Как вы поймёте, что задача решена?",
            }),
            "contact": forms.TextInput(attrs={
                "placeholder": "Email, телефон или контакт в мессенджере",
            }),
            "interaction_format": forms.TextInput(attrs={
                "placeholder": "Например, онлайн-консультация, совместная работа или «Обсудим»",
            }),
        }
        help_texts = {
            "title": "Краткое название задачи. До 200 символов.",
            "description": "Опишите текущую ситуацию своими словами. До 5000 символов.",
            "need": "Укажите, чего не хватает для решения задачи. До 5000 символов.",
            "expected_result": "Опишите желаемый результат. До 2000 символов.",
            "contact": "Один удобный способ связи. Для мессенджера укажите его название.",
            "interaction_format": "Свободный текст: готовых вариантов выбирать не нужно.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # blank=True в модели нужен для совместимости со старыми записями.
            # Здесь все шесть полей обязательны, в том числе при редактировании.
            field.required = True
            field.error_messages["required"] = "Заполните это поле."
            field.error_messages["max_length"] = (
                "Слишком длинный текст. Максимум — %(limit_value)s символов."
            )

class ProposalForm(forms.Form):
    solution = forms.CharField(
        min_length=10,
        max_length=5000,
        strip=True,
        widget=forms.Textarea,
    )