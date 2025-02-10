import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm

HOME_URL = reverse('news:home')


@pytest.mark.django_db
def test_news_count(client, create_news):
    """Количество новостей на главной странице соответствует настройкам."""
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, create_news):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    response = client.get(HOME_URL)
    object_list = response.context['object_list']

    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, detail_url, create_comments):
    """
    Комментарии на странице отдельной новости отсортированы
    в хронологическом порядке: старые в начале списка, новые — в конце.
    """
    response = client.get(detail_url)
    assert 'news' in response.context

    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detail_url):
    """Анонимному пользователю не доступна форма для отправки комментария."""
    response = client.get(detail_url)
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, detail_url):
    """Авторизованному пользователю доступна форма для отправки комментария."""
    response = author_client.get(detail_url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
