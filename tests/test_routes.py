from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
            )


    def test_pages_availability(self):
        """Тест доступности страниц без авторизации"""
        urls = (
            ('notes:home', None, HTTPStatus.OK),
            ('notes:list', None, HTTPStatus.FOUND),
            ('notes:detail', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:add', None, HTTPStatus.FOUND),
            ('notes:edit', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:delete', (self.note.slug,), HTTPStatus.FOUND),
            ('notes:success', None, HTTPStatus.FOUND),
        )
        for name, args, expected_status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)
                
    def test_pages_availability(self):
        """Тест доступности страниц c авторизацией"""
        self.client.force_login(self.author)
        urls = (
            ('notes:list', None, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), HTTPStatus.OK),
            ('notes:add', None, HTTPStatus.OK),
            ('notes:edit', (self.note.slug,), HTTPStatus.OK),
            ('notes:delete', (self.note.slug,), HTTPStatus.OK),
            ('notes:success', None, HTTPStatus.OK),
        )
        for name, args, expected_status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)
                
    def test_availability_for_different_users(self):
        """Тест доступности страниц редактирования и удаления заметки для разных пользователей"""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, expected_status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:delete'):  
                with self.subTest(user=user, name=name):        
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)
                    
    def test_redirect_for_anonymous_client(self):
        """Тест редиректа неавторизованного пользователя"""
        login_url = reverse('users:login')
        urls = (
            'notes:edit',
            'notes:delete',
            'notes:add',
            'notes:success',
            'notes:list',
        )
        for name in urls:
            with self.subTest(name=name):
                args = (self.note.slug,) if name in ('notes:edit', 'notes:delete') else None
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
                
    def test_404_for_nonexistent_url(self):
        """Тест для несуществующего маршрута, должен вернуть 404"""
        response = self.client.get('/notes/nonexistent-url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
