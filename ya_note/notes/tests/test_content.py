from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNotePage(TestCase):

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

        cls.notes_list_url = reverse('notes:list')
        cls.note_add_url = reverse('notes:add')
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_notes_list_for_different_users(self):
        """
        В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        client_access = (
            (self.author_client, True),
            (self.not_author_client, False)
        )
        for client, access in client_access:
            with self.subTest(name=client):
                response = client.get(self.notes_list_url)
                self.assertIn('object_list', response.context)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, access)

    def test_pages_contains_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            self.note_add_url,
            self.note_edit_url
        )
        for url in urls:
            with self.subTest():
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
