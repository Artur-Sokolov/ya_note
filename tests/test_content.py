from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()

class TestHomePage(TestCase):
    HOME_URL = reverse('notes:home')

class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1')
        cls.user2 = User.objects.create(username='user2')
        cls.note1 = Note.objects.create(
            title='Зметка пользователя 1',
            text='Просто текст1.',
            author=cls.user1,
        )
        cls.note2 = Note.objects.create(
            title='Зметка пользователя 2',
            text='Просто текст2.',
            author=cls.user2,
        )
        cls.list_url = reverse('notes:list')
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note1.slug))
        
    def test_note_appears_in_object_list(self):
        """Проверяем, что заметка отображается в object_list у своего автора."""
        self.client.force_login(self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        self.assertIn(self.note1, object_list)
        self.assertNotIn(self.note2, object_list)
        
    def test_user_see_only_his_own_notes(self):
        """Проверяем, что пользователь видит только свои заметки."""
        self.client.force_login(self.user2)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        self.assertIn(self.note2, object_list)
        self.assertNotIn(self.note1, object_list)
        
    def test_anonymous_client_has_no_form(self):
        response_add = self.client.get(self.add_url)
        response_edit = self.client.get(self.edit_url)
        self.assertNotIn('form', response_add.context)
        self.assertNotIn('form', response_edit.context)
        
    def test_authorized_client_has_form(self):
        self.client.force_login(self.user1)
        response_add = self.client.get(self.add_url)
        response_edit = self.client.get(self.edit_url)
        self.assertIn('form', response_add.context)
        self.assertIsInstance(response_add.context['form'], NoteForm)
        self.assertIn('form', response_edit.context)
        self.assertIsInstance(response_edit.context['form'], NoteForm)