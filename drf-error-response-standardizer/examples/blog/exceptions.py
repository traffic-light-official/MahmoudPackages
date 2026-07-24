"""Example domain exception for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from drf_error_response_standardizer.exceptions import ProblemAPIException


class ArticleAlreadyPublishedError(ProblemAPIException):
    """Raised when attempting to edit a published :class:`~examples.blog.models.Article`."""

    status_code = 409
    default_detail = "Published articles cannot be edited."
    default_code = "article_already_published"
    title = "Article Already Published"
    type_slug = "article-already-published"
