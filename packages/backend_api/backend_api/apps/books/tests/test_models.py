from datetime import timedelta

import shortuuid

from django.test import TestCase
from django.utils import timezone

from apps.books.models import Book, BorrowedBook

class TestBookModel(TestCase):
    def setUp(self):
        self.user_id = f'user_{shortuuid.uuid()}'
        self.book = Book.objects.create(
            id=f'book_{shortuuid.uuid()}',
            title='To Kill a Mockingbird',
            author='Harper Lee',
            added_by=self.user_id,
            isbn='9780061120084',
            category='Fiction',
            publisher='HarperCollins',
        )

    def test_book_creation(self):
        self.assertTrue(isinstance(self.book, Book))
        self.assertEqual(self.book.category, 'Fiction')
        self.assertEqual(self.book.author, 'Harper Lee')
        self.assertTrue(self.book.id.startswith('book_'))
        self.assertEqual(self.book.isbn, '9780061120084')
        self.assertEqual(self.book.publisher, 'HarperCollins')
        self.assertTrue(self.book.added_by.startswith('user_'))
        self.assertEqual(self.book.title, 'To Kill a Mockingbird')

    def test_book_str_method(self):
        self.assertEqual(str(self.book), 'To Kill a Mockingbird')

    def test_book_is_available(self):
        self.assertTrue(self.book.is_available())

        BorrowedBook.objects.create(
            book=self.book,
            id=f'borrowed_{shortuuid.uuid()}',
            borrower=f'user_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        self.assertFalse(self.book.is_available())

    def test_book_current_borrowing(self):
        self.assertIsNone(self.book.current_borrowing())

        borrowed_book = BorrowedBook.objects.create(
            book=self.book,
            id=f'borrowed_{shortuuid.uuid()}',
            borrower=f'user_{shortuuid.uuid()}',
            proposed_return_date=timezone.now() + timedelta(days=14),
        )
        self.assertEqual(self.book.current_borrowing(), borrowed_book)