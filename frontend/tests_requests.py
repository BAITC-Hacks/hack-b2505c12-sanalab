"""Запуск: python manage.py test frontend.tests_requests

Тесты используют отдельную тестовую базу Django, а не данные вашего сайта.
"""
from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from backend.models import BusinessRequest
from .forms import BusinessRequestForm


class RequestWorkflowTests(TestCase):
    def setUp(self):
        self.payload = {
            "title": "Онлайн-запись клиентов",
            "description": "Сейчас сотрудники записывают клиентов вручную.",
            "need": "Нужна форма записи и единое расписание.",
            "expected_result": "Клиенты выбирают свободное время самостоятельно.",
            "contact": "Telegram: @example_contact",
            "interaction_format": "Совместная работа онлайн; детали обсудим.",
        }
        self.create_url = reverse("frontend:business_request")

    def create_request(self, client=None, **extra):
        browser = client if client is not None else self.client
        response = browser.post(self.create_url, {**self.payload, **extra})
        self.assertEqual(response.status_code, 302)
        item = BusinessRequest.objects.latest("pk")
        self.assertEqual(response.url, reverse("frontend:request_detail", args=[item.pk]))
        return item

    def confirm_request(self, item):
        return self.client.post(
            reverse("frontend:request_confirm", args=[item.pk]),
            {"revision": item.revision, "confirm": "yes"},
        )

    def test_form_has_exactly_six_free_text_fields(self):
        form = BusinessRequestForm()
        self.assertEqual(list(form.fields), list(self.payload))
        for field in form.fields.values():
            self.assertTrue(field.required)
            self.assertIsInstance(field.widget, (forms.TextInput, forms.Textarea))
            self.assertNotIsInstance(field.widget, (forms.EmailInput, forms.Select))
        self.assertTrue(BusinessRequestForm(self.payload).is_valid())

    def test_form_page_has_all_fields_and_csrf(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        for name in self.payload:
            self.assertContains(response, f'name="{name}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_all_fields_are_required_even_for_whitespace(self):
        for name in self.payload:
            with self.subTest(field=name):
                form = BusinessRequestForm({**self.payload, name: "   "})
                self.assertFalse(form.is_valid())
                self.assertIn(name, form.errors)

    def test_server_enforces_text_limits(self):
        form = BusinessRequestForm({**self.payload, "title": "a" * 201})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_create_saves_draft_and_ignores_client_status(self):
        item = self.create_request(status="confirmed", owner_key="x" * 64, revision=999)
        self.assertEqual(item.status, BusinessRequest.Status.DRAFT)
        self.assertIsNone(item.confirmed_at)
        self.assertEqual(item.revision, 1)
        self.assertEqual(len(item.owner_key), 64)
        self.assertNotEqual(item.owner_key, "x" * 64)

    def test_invalid_create_keeps_entered_text_and_saves_nothing(self):
        response = self.client.post(self.create_url, {**self.payload, "need": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BusinessRequest.objects.count(), 0)
        self.assertContains(response, self.payload["title"])
        self.assertIn("need", response.context["form"].errors)

    def test_card_shows_all_values_without_confirming(self):
        item = self.create_request()
        response = self.client.get(reverse("frontend:request_detail", args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        for value in self.payload.values():
            self.assertContains(response, value)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
        self.assertEqual(item.revision, 1)

    def test_card_escapes_entered_html(self):
        item = self.create_request(title='<script>alert("x")</script>')
        response = self.client.get(reverse("frontend:request_detail", args=[item.pk]))
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, "&lt;script&gt;")

    def test_edit_page_is_prepopulated(self):
        item = self.create_request()
        response = self.client.get(reverse("frontend:request_edit", args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        for name, value in self.payload.items():
            self.assertEqual(response.context["form"][name].value(), value)
        self.assertContains(response, 'name="revision" value="1"')

    def test_edit_updates_same_record_not_new_record(self):
        item = self.create_request()
        response = self.client.post(
            reverse("frontend:request_edit", args=[item.pk]),
            {**self.payload, "title": "Обновлённая задача", "revision": item.revision},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BusinessRequest.objects.count(), 1)
        item.refresh_from_db()
        self.assertEqual(item.title, "Обновлённая задача")
        self.assertEqual(item.revision, 2)
        self.assertEqual(item.status, "draft")

    def test_invalid_edit_does_not_change_saved_record(self):
        item = self.create_request()
        response = self.client.post(
            reverse("frontend:request_edit", args=[item.pk]),
            {**self.payload, "need": "", "revision": item.revision},
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.need, self.payload["need"])
        self.assertEqual(item.revision, 1)

    def test_confirm_requires_post(self):
        item = self.create_request()
        response = self.client.get(reverse("frontend:request_confirm", args=[item.pk]))
        self.assertEqual(response.status_code, 405)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")

    def test_confirm_requires_checked_box(self):
        item = self.create_request()
        response = self.client.post(
            reverse("frontend:request_confirm", args=[item.pk]),
            {"revision": item.revision},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
        self.assertIsNone(item.confirmed_at)

    def test_manual_confirmation_persists_status_and_time(self):
        item = self.create_request()
        self.assertEqual(self.confirm_request(item).status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, "confirmed")
        self.assertIsNotNone(item.confirmed_at)
        self.assertEqual(item.revision, 2)

    def test_repeated_confirmation_is_idempotent(self):
        item = self.create_request()
        self.confirm_request(item)
        item.refresh_from_db()
        first_time, first_version = item.confirmed_at, item.revision
        self.confirm_request(item)
        item.refresh_from_db()
        self.assertEqual(item.confirmed_at, first_time)
        self.assertEqual(item.revision, first_version)

    def test_editing_confirmed_card_resets_confirmation(self):
        item = self.create_request()
        self.confirm_request(item)
        item.refresh_from_db()
        response = self.client.post(
            reverse("frontend:request_edit", args=[item.pk]),
            {**self.payload, "need": "Новая потребность", "revision": item.revision},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
        self.assertIsNone(item.confirmed_at)
        self.assertEqual(item.need, "Новая потребность")
        self.assertEqual(item.revision, 3)

    def test_stale_edit_cannot_overwrite_newer_data(self):
        item = self.create_request()
        url = reverse("frontend:request_edit", args=[item.pk])
        self.client.post(url, {**self.payload, "title": "Новая версия", "revision": 1})
        response = self.client.post(url, {**self.payload, "title": "Старая вкладка", "revision": 1})
        self.assertEqual(response.status_code, 409)
        self.assertContains(response, "Старая вкладка", status_code=409)
        item.refresh_from_db()
        self.assertEqual(item.title, "Новая версия")
        self.assertEqual(item.revision, 2)

    def test_stale_card_cannot_confirm_newer_data(self):
        item = self.create_request()
        self.client.post(
            reverse("frontend:request_edit", args=[item.pk]),
            {**self.payload, "title": "Новая версия", "revision": 1},
        )
        # item.revision всё ещё 1: имитируем кнопку в старой вкладке.
        self.confirm_request(item)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
        self.assertIsNone(item.confirmed_at)

    def test_incomplete_saved_record_cannot_be_confirmed(self):
        item = self.create_request()
        BusinessRequest.objects.filter(pk=item.pk).update(need="")
        response = self.confirm_request(item)
        self.assertEqual(response.url, reverse("frontend:request_edit", args=[item.pk]))
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")

    def test_other_session_cannot_read_edit_or_confirm_card(self):
        item = self.create_request()
        stranger = Client()
        for name in ("request_detail", "request_edit"):
            response = stranger.get(reverse(f"frontend:{name}", args=[item.pk]))
            self.assertEqual(response.status_code, 404)
        response = stranger.post(
            reverse("frontend:request_edit", args=[item.pk]),
            {**self.payload, "title": "Чужая правка", "revision": 1},
        )
        self.assertEqual(response.status_code, 404)
        response = stranger.post(
            reverse("frontend:request_confirm", args=[item.pk]),
            {"confirm": "yes", "revision": 1},
        )
        self.assertEqual(response.status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.title, self.payload["title"])
        self.assertEqual(item.status, "draft")

    def test_list_only_shows_current_session_requests(self):
        item = self.create_request()
        list_url = reverse("frontend:request_list")
        self.assertContains(self.client.get(list_url), item.title)
        response = Client().get(list_url)
        self.assertNotContains(response, item.title)
        self.assertContains(response, "Здесь пока нет заявок")

    def test_legacy_unowned_record_is_not_exposed(self):
        old_item = BusinessRequest.objects.create(**self.payload)
        response = self.client.get(reverse("frontend:request_detail", args=[old_item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(BusinessRequest.objects.filter(pk=old_item.pk).exists())

    def test_csrf_is_required_for_create_and_confirm(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.create_url, self.payload).status_code, 403)
        item = self.create_request()
        strict.cookies = self.client.cookies
        response = strict.post(
            reverse("frontend:request_confirm", args=[item.pk]),
            {"confirm": "yes", "revision": item.revision},
        )
        self.assertEqual(response.status_code, 403)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
