from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from news.models import Comment
from news.forms import BAD_WORDS, WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, detail_url):
    """Анонимный пользователь не может создать комментарий."""
    client.post(detail_url, data=form_data)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(
        author_client, form_data, news, author, detail_url, url_to_comments
):
    """Залогиненный пользователь может оставить комментарий."""
    response = author_client.post(detail_url, data=form_data)
    assertRedirects(response, url_to_comments)
    assert Comment.objects.count() == 1

    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.author == author
    assert comment.news == news


@pytest.mark.parametrize(
    'bad_word', BAD_WORDS
)
def test_user_cant_use_bad_words(bad_word, author_client, detail_url):
    """
    Пользователь не может использовать запрещённые слова
    при комментировании.
    """
    bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}
    response = author_client.post(detail_url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    assert Comment.objects.count() == 0


def test_author_cat_edit_comment(
    author_client, edit_url, url_to_comments, form_data, comment
):
    """Редактирование комментария доступно для автора."""
    comment_from_db = Comment.objects.get(id=comment.id)
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)

    comment.refresh_from_db()
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author
    assert comment.text == form_data['text']
    assert comment.created == comment_from_db.created


def test_user_cant_edit_comment_of_another_user(
    not_author_client, edit_url, form_data, comment
):
    """Редактирование комментария недоступно для другого пользователя."""
    response = not_author_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author
    assert comment.text == comment_from_db.text
    assert comment.created == comment_from_db.created


def test_author_can_delete_comment(
    author_client, delete_url, url_to_comments
):
    """Автор может удалить свой комментарий."""
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    assert Comment.objects.count() == 0


def test_user_cant_delete_comment_of_another_user(
    not_author_client, delete_url
):
    """Пользователь не может удалить чужой комментарий."""
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
