"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

pytest_plugins = ["pytester"]


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def minimal_openapi() -> dict[str, Any]:
    """A tiny-but-realistic OpenAPI document, for hand-crafted rule tests."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/articles/": {
                "get": {
                    "operationId": "listArticles",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Article"}
                                }
                            }
                        }
                    },
                },
                "post": {
                    "operationId": "createArticle",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ArticleRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Article"}
                                }
                            }
                        }
                    },
                },
            }
        },
        "components": {
            "schemas": {
                "Article": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "status": {"type": "string", "enum": ["draft", "published"]},
                    },
                    "required": ["id", "title", "status"],
                },
                "ArticleRequest": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "status": {"type": "string", "enum": ["draft", "published"]},
                    },
                    "required": ["title"],
                },
            }
        },
    }
