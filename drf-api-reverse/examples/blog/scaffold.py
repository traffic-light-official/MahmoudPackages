"""Example: scaffold this directory's contract into a temp app and print the result.

Run with:

    python -m examples.blog.scaffold
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from drf_api_reverse import load_schema_file, scaffold

HERE = Path(__file__).parent


def main() -> None:
    """Scaffold ``contract.yml`` into a temporary directory and print the result."""
    schema = load_schema_file(HERE / "contract.yml")

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "myapp"
        for result in scaffold(schema, output_dir):
            verb = "Created" if result.created else "Updated"
            print(f"{verb} {output_dir / result.filename}")


if __name__ == "__main__":
    main()
