"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory

from tests.test_app.models import Article, Author, Comment, Profile, Tag


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def author(db: None) -> Author:
    return Author.objects.create(name="Ada Lovelace", email="ada@example.com", bio="Mathematician")


@pytest.fixture
def profile(db: None, author: Author) -> Profile:
    return Profile.objects.create(
        author=author, display_name="Ada L.", avatar_url="https://example.com/a.png"
    )


@pytest.fixture
def tags(db: None) -> list[Tag]:
    return list(
        Tag.objects.bulk_create(
            [Tag(label="python"), Tag(label="django"), Tag(label="performance")]
        )
    )


@pytest.fixture
def article(db: None, author: Author, tags: list[Tag]) -> Article:
    article = Article.objects.create(
        title="Sparse Fieldsets", body="...", author=author, view_count=42
    )
    article.tags.set(tags[:2])
    Comment.objects.create(article=article, author_name="Bob", text="Great post!")
    Comment.objects.create(article=article, author_name="Carol", text="Thanks!")
    return article


@pytest.fixture
def many_articles(db: None, author: Author, tags: list[Tag]) -> list[Article]:
    articles = []
    for i in range(5):
        a = Article.objects.create(title=f"Article {i}", body="...", author=author)
        a.tags.set(tags[:1])
        articles.append(a)
    return articles
