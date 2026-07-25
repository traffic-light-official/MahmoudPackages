# Getting Started

## Install

```bash
pip install drf-api-reverse
```

## Write (or obtain) an OpenAPI contract

Any OpenAPI 3.x document works. A minimal one:

```yaml
openapi: 3.0.3
info:
  title: Blog API
  version: "1.0.0"
components:
  schemas:
    Article:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
      required:
        - title
paths:
  /articles/:
    get:
      operationId: listArticles
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Article"
  /articles/{id}/:
    get:
      operationId: retrieveArticle
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Article"
```

## Scaffold

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

```
Created myapp/serializers.py
Created myapp/views.py
Created myapp/urls.py
```

Wire `myapp/urls.py` into your project's root `urlpatterns` as usual
(`include("myapp.urls")`), and fill in the `raise NotImplementedError`
method bodies in `myapp/views.py` with your real logic.

## Regenerate whenever the contract changes

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

Anything you wrote - inside a generated file but outside its marked
regions, or in the method bodies themselves once you've replaced the
`raise` - survives. Only the parts that mechanically follow from the
schema (field lists, method signatures, router registrations) are
regenerated. See [Architecture](architecture.md) for exactly what is
and isn't touched.

## Gate CI on drift

```bash
drf-api-reverse check --schema api/contract.yml --output myapp/
```

Exits `1` if the committed generated code no longer matches what the
current contract would produce - see [Deployment](deployment.md).
