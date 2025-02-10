from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNotePage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не Автор')

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_notes_list_for_different_users(self):
        """
        В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        users = (
            (self.author, True),
            (self.not_author, False)
        )
        for name, status in users:
            self.client.force_login(name)
            url = reverse('notes:list')
            response = self.client.get(url)
            object_list = response.context['object_list']
            self.assertEqual(self.note in object_list, status)

    def test_pages_contains_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            self.client.force_login(self.author)
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
