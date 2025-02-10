from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteCreation(TestCase):

    NOTE_TITLE = 'Название заметки'
    NOTE_TEXT = 'Текст'
    NOTE_SLUG = 'Slug'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.redirect_url = reverse('notes:success')
        cls.author = User.objects.create(username='Пользователь')
        cls.not_author = User.objects.create(username='Не Автор')

        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)

        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
            'author': cls.author
        }

        cls.note = None

    def create_note(self):
        """Создает заметку."""
        self.note = Note.objects.create(
            title=self.NOTE_TITLE,
            text=self.NOTE_TEXT,
            slug=self.NOTE_SLUG,
            author=self.author
        )

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        self.client.post(self.url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        response = self.auth_client.post(self.url, data=self.form_data)

        self.assertRedirects(response, self.redirect_url)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.author)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.create_note()

        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug, то он
        формируется автоматически из названия заметки.
        """
        self.form_data.pop('slug')
        self.auth_client.post(self.url, data=self.form_data)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может редактировать заметку."""
        self.create_note()

        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.post(url, self.form_data)
        self.assertRedirects(response, self.redirect_url)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """
        Зарегистрированный пользователь не может редактировать
        чужую заметку.
        """
        self.create_note()

        self.auth_client.force_login(self.not_author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        self.create_note()

        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.post(url)
        self.assertRedirects(response, self.redirect_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Зарегистрированный пользователь не может удалить чужую заметку."""
        self.create_note()

        self.auth_client.force_login(self.not_author)

        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
