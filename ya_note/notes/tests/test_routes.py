from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

NOTE_ADD_SUCCESS_URLS = (
    'notes:list',
    'notes:add',
    'notes:success'
)


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не Автор')

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_pages_availability(self):
        """
        Пользователям доступны главная страница, страницы регистрации,
        входа и выхода из учетной записи.
        """
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup'
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_edit_delete_access_permissions(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы попытается
        зайти другой пользователь — вернётся ошибка 404.
        """
        user_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND)
        )
        urls = (
            'notes:detail',
            'notes:edit',
            'notes:delete'
        )

        for user, status in user_statuses:
            self.client.force_login(user)

            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница
        со списком заметок, страница успешного добавления заметки,
        страница добавления новой заметки.
        """
        self.client.force_login(self.not_author)
        for name in NOTE_ADD_SUCCESS_URLS:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        for name in NOTE_ADD_SUCCESS_URLS:
            with self.subTest(name=name):
                url = reverse(name)
                redirect_url = f'{settings.LOGIN_URL}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
