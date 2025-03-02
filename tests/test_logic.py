from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify
from notes.models import Note

User = get_user_model()

class TestNoteLogic(TestCase):
    NOTE_TEXT = 'Текст комментария'
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1')
        cls.author = User.objects.create_user(username='author')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        
        cls.other_client = Client()
        cls.other_client.force_login(cls.user1)
        
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.note_data = {'title': 'Новая заметка',
                         'text': 'Какой-то текст', 'slug': 'new-note'}
        cls.duplicate_note_data = {
            'title': 'Дубликат',
            'text': 'Текст заметки',
            'slug': 'unique-slug'
        }
        cls.note_data_empty_slug = {'title': 'Новая заметка',
                         'text': 'Какой-то текст', 'slug': ''}
        
    def test_anonymus_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(self.add_url, data=self.note_data)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={self.add_url}')
        self.assertFalse(Note.objects.filter(slug='new-note').exists())

    def test_user_cant_create_note_with_duplicate_slug(self):
        """Пользователь не может создать заметку с уже существующим slug."""
        Note.objects.create(
            title='Заголовок',
            text='Какой-то текст',
            author=self.author,
            slug='unique-slug'
            )
        response = self.auth_client.post(self.add_url, data=self.duplicate_note_data)
        self.assertEqual(Note.objects.filter(slug='unique-slug').count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
    def test_slug_is_generated_if_empty(self):
        """Если slug не заполнен, он создаётся автоматически."""
        responce = self.auth_client.post(self.add_url, data=self.note_data_empty_slug)
        self.assertEqual(responce.status_code, HTTPStatus.FOUND)
        expected_slug = slugify(self.note_data_empty_slug['title'])[:100]
        self.assertTrue(Note.objects.filter(slug=expected_slug).exists())
        
    def test_user_can_edit_and_delete_own_notes_but_not_others(self):
        """Пользователь может редактировать и удалять свои заметки, но не чужие."""
        edit_response = self.other_client.post(self.edit_url,data=self.note_data)
        self.assertEqual(edit_response.status_code, HTTPStatus.NOT_FOUND)
        
        delete_response = self.other_client.post(self.delete_url)
        self.assertEqual(delete_response.status_code, HTTPStatus.NOT_FOUND)
        
        self.auth_client.post(self.edit_url, {'title': 'Новая',
                                              'text': 'Какой-то текст'})
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Новая')
        
        self.auth_client.post(self.delete_url)
        self.assertFalse(Note.objects.filter(slug='unique-slug').exists())