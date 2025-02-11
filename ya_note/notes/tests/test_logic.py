from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Пользователь')
        cls.not_author = User.objects.create(username='Не Автор')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Новый текст',
            'slug': 'New_note',
        }

        cls.note = Note.objects.create(
            title='Заметка',
            text='Текст',
            slug='Note',
            author=cls.author
        )

        cls.add_note_url = reverse('notes:add')
        cls.edit_note_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_note_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        count_notes = Note.objects.count()
        self.client.post(self.add_note_url, data=self.form_data)
        self.assertEqual(Note.objects.count(), count_notes)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        Note.objects.all().delete()
        response = self.author_client.post(
            self.add_note_url, data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        count_notes = Note.objects.count()
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(
            self.add_note_url, data=self.form_data
        )
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), count_notes)

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug, то он
        формируется автоматически из названия заметки.
        """
        Note.objects.all().delete()
        self.form_data.pop('slug')
        self.author_client.post(self.add_note_url, data=self.form_data)
        note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может редактировать заметку."""
        response = self.author_client.post(self.edit_note_url, self.form_data)
        self.assertRedirects(response, self.success_url)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])
        self.assertEqual(self.note.author, self.author)

    def test_other_user_cant_edit_note(self):
        """
        Зарегистрированный пользователь не может редактировать
        чужую заметку.
        """
        note_before_request = Note.objects.get(id=self.note.id)
        response = self.not_author_client.post(
            self.edit_note_url, self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertEqual(note_before_request.title, self.note.title)
        self.assertEqual(note_before_request.text, self.note.text)
        self.assertEqual(note_before_request.slug, self.note.slug)
        self.assertEqual(note_before_request.author, self.note.author)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        count_notes = Note.objects.count()
        response = self.author_client.post(self.delete_note_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), count_notes - 1)

    def test_other_user_cant_delete_note(self):
        """Зарегистрированный пользователь не может удалить чужую заметку."""
        count_notes = Note.objects.count()
        response = self.not_author_client.post(self.delete_note_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), count_notes)
