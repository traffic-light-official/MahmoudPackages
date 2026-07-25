# Performance

## Scaffolding is O(schema size), not O(project size)

`scaffold()` walks exactly the given schema document - component
schemas once each, paths once each - and writes exactly three files. It
never scans the target Django project, imports any of your existing
code, or touches the database. Cost scales with the size of the OpenAPI
contract, not with how large the app you're scaffolding into is.

## Region merging is a single linear pass per file

`regions.parse_regions()` and `regions.merge()` both do one pass over
the existing file's lines - there is no repeated re-scanning per region
and no quadratic behavior as the number of regions grows. For contracts
with hundreds of component schemas and resources, merging remains a
single-digit-millisecond operation dominated by file I/O, not by the
region-matching logic itself.

## Dependency ordering is a single topological sort

Serializer class ordering (`codegen.serializers._emission_order`) runs
`graphlib.TopologicalSorter` once over the full dependency graph, not
once per class - `$ref` resolution itself is a single dict lookup per
field (`type_mapping.ref_target`), with no repeated parsing of the
`$ref` string beyond a simple prefix check.

## CI cost is dominated by installing the package, not running it

In a typical `check`/`scaffold` CI step, `pip install drf-api-reverse`
takes far longer than the scaffold/check operation itself, which
completes in well under a second for realistically-sized contracts (up
to several hundred operations). If install time matters, pin the
version and let your CI's dependency cache handle repeat installs
across runs - there is nothing to tune in this package's own runtime
behavior.

## No network access, no subprocess, no database

Unlike the sibling `drf-changelog-generator` package (which shells out
to `git show` to read historical schema versions), this package never
invokes a subprocess and never needs network access - `--schema` is
always a local file (or, programmatically, an already-loaded dict).
There is no I/O beyond reading the schema file and writing the three
generated files.
