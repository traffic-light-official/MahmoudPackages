"""Shared fixtures for the drf-api-reverse test suite."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_schema() -> dict[str, Any]:
    """A small but representative OpenAPI document.

    Covers: a referenced nested schema (``Author``), an enum field, an
    array-of-primitives field, an array-of-``$ref`` field, a
    date-time-formatted field, standard collection/detail CRUD paths,
    and one nested sub-resource path.
    """
    return {
        "openapi": "3.0.3",
        "info": {"title": "Sample API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Author": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "display_name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["display_name", "email"],
                },
                "Article": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["draft", "published", "archived"],
                        },
                        "author": {"$ref": "#/components/schemas/Author"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "published_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["title", "status"],
                },
                "Comment": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "body": {"type": "string"},
                        "author": {"$ref": "#/components/schemas/Author"},
                    },
                    "required": ["body"],
                },
            }
        },
        "paths": {
            "/articles/": {
                "get": {
                    "operationId": "listArticles",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Article"},
                                    }
                                }
                            }
                        }
                    },
                },
                "post": {
                    "operationId": "createArticle",
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Article"}}
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
            },
            "/articles/{id}/": {
                "get": {
                    "operationId": "retrieveArticle",
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
                "patch": {
                    "operationId": "partialUpdateArticle",
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
                "delete": {"operationId": "deleteArticle", "responses": {"204": {}}},
            },
            "/articles/{id}/comments/": {
                "get": {
                    "operationId": "listArticleComments",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Comment"},
                                    }
                                }
                            }
                        }
                    },
                }
            },
        },
    }
