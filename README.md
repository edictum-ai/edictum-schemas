# edictum-schemas

Single source of truth for the Edictum contract bundle JSON Schema, consumed by both the Python library ([edictum](https://pypi.org/project/edictum/)) and the TypeScript library (edictum-ts).

## Schema

The schema defines the structure for Edictum YAML contract bundles (`edictum/v1` `ContractBundle`), including pre/post/session/sandbox contract types, expression operators, and observability configuration.

## Install

### Node.js (pnpm)

```bash
pnpm add @edictum/schemas
```

```js
import schema from "@edictum/schemas";
```

### Python (pip / uv)

```bash
pip install edictum-schemas
# or
uv add edictum-schemas
```

```python
from edictum_schemas import load_schema, schema_path

schema = load_schema()       # dict
path = schema_path()         # pathlib.Path
```

## License

MIT
