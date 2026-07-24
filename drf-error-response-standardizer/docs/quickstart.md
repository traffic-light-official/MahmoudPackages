# Quick Start

A complete, runnable example: a blog API where creating an `Article`
validates a nested, writable `author` serializer, and a domain rule
("cannot edit a published article") is enforced with a custom problem
type.

## Models and serializers

```python
# blog/models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)
```

```python
# blog/serializers.py
from rest_framework import serializers

from blog.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author", "published"]

    def create(self, validated_data):
        author_data = validated_data.pop("author")
        author = Author.objects.create(**author_data)
        return Article.objects.create(author=author, **validated_data)
```

## A domain-specific problem

```python
# blog/exceptions.py
from drf_error_response_standardizer.exceptions import ProblemAPIException


class ArticleAlreadyPublishedError(ProblemAPIException):
    status_code = 409
    default_detail = "Published articles cannot be edited."
    default_code = "article_already_published"
    title = "Article Already Published"
    type_slug = "article-already-published"
```

```python
# blog/views.py
from rest_framework import viewsets

from blog.exceptions import ArticleAlreadyPublishedError
from blog.models import Article
from blog.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer

    def perform_update(self, serializer):
        if serializer.instance.published:
            raise ArticleAlreadyPublishedError(extensions={"article_id": serializer.instance.id})
        serializer.save()
```

## Settings

```python
# settings.py
MIDDLEWARE = [
    "drf_error_response_standardizer.middleware.CorrelationIdMiddleware",
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": (
        "drf_error_response_standardizer.handler.problem_details_exception_handler"
    ),
}
```

## Requests and responses

Missing a required nested field:

```http
POST /articles/
Content-Type: application/json

{"title": "Hello", "body": "...", "author": {"name": "Ada"}}
```

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/articles/",
  "code": "validation_error",
  "errors": [
    { "pointer": "author/email", "detail": "This field is required.", "code": "required" }
  ]
}
```

Editing a published article:

```http
PATCH /articles/1/
Content-Type: application/json

{"title": "New title"}
```

```json
{
  "type": "about:blank",
  "title": "Article Already Published",
  "status": 409,
  "detail": "Published articles cannot be edited.",
  "instance": "/articles/1/",
  "code": "article_already_published",
  "article_id": 1
}
```

See [Advanced Usage](advanced-usage.md) for the error catalog, OpenAPI
integration, and localization.
