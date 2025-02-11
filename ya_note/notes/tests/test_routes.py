from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не Автор')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

        cls.home_url = reverse('notes:home')

        cls.notes_list_url = reverse('notes:list')
        cls.note_detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.note_add_url = reverse('notes:add')
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.note_delete_url = reverse('notes:delete', args=(cls.note.slug,))

        cls.login_url = reverse('users:login')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')

        cls.success_url = reverse('notes:success')

    def test_pages_availability(self):
        """
        Пользователям доступны главная страница, страницы регистрации,
        входа и выхода из учетной записи.
        """
        urls = (
            self.home_url,
            self.login_url,
            self.logout_url,
            self.signup_url
        )
        for url in urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_edit_delete_access_permissions(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается
        зайти другой пользователь — вернётся ошибка 404.
        """
        user_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.not_author_client, HTTPStatus.NOT_FOUND)
        )
        urls = (
            self.note_detail_url,
            self.note_edit_url,
            self.note_delete_url,
        )

        for user, status in user_statuses:
            for url in urls:
                with self.subTest():
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница
        со списком заметок, страница успешного добавления заметки,
        страница добавления новой заметки.
        """
        urls = (
            self.notes_list_url,
            self.note_add_url,
            self.success_url
        )
        for url in urls:
            with self.subTest():
                response = self.not_author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        urls = (
            self.notes_list_url,
            self.note_add_url,
            self.success_url
        )
        for url in urls:
            with self.subTest():
                redirect_url = f'{settings.LOGIN_URL}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
