"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def old_schema() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Article": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "legacy_id": {"type": "string"},
                    },
                    "required": ["title"],
                }
            }
        },
        "paths": {
            "/articles/": {
                "get": {
                    "operationId": "listArticles",
                    "parameters": [
                        {
                            "name": "search",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        }
                    ],
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
                "delete": {
                    "operationId": "deleteArticle",
                    "responses": {"204": {}},
                }
            },
        },
    }


@pytest.fixture
def new_schema() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.1.0"},
        "components": {
            "schemas": {
                "Article": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "tags"],
                }
            }
        },
        "paths": {
            "/articles/": {
                "get": {
                    "operationId": "listArticles",
                    "parameters": [],
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
                    "deprecated": True,
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
            "/articles/{id}/comments/": {
                "get": {
                    "operationId": "listComments",
                    "responses": {"200": {}},
                }
            },
        },
    }


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A real Git repository with a schema file committed at two tags."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    run("init", "-b", "main")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")

    schema_v1 = {
        "openapi": "3.0.3",
        "paths": {"/articles/": {"get": {"operationId": "listArticles", "responses": {"200": {}}}}},
    }
    (repo / "schema.yml").write_text(yaml.safe_dump(schema_v1), encoding="utf-8")
    run("add", "schema.yml")
    run("commit", "-m", "v1")
    run("tag", "v1.0.0")

    schema_v2 = {
        "openapi": "3.0.3",
        "paths": {
            "/articles/": {"get": {"operationId": "listArticles", "responses": {"200": {}}}},
            "/comments/": {"get": {"operationId": "listComments", "responses": {"200": {}}}},
        },
    }
    (repo / "schema.yml").write_text(yaml.safe_dump(schema_v2), encoding="utf-8")
    run("add", "schema.yml")
    run("commit", "-m", "v2")
    run("tag", "v2.0.0")

    return repo
