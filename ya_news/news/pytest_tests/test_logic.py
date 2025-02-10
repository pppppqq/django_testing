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


def test_user_cant_use_bad_words(author_client, detail_url):
    """
    Пользователь не может использовать запрещённые слова
    при комментировании.
    """
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
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
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
    not_author_client, edit_url, form_data, comment
):
    """Редактирование комментария недоступно для другого пользователя."""
    response = not_author_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment.refresh_from_db()
    assert comment.text != form_data['text']


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
