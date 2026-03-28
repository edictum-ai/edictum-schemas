# edictum-schemas

Single source of truth for the Edictum ruleset JSON Schema, consumed by the Python library ([edictum](https://pypi.org/project/edictum/)), TypeScript library (edictum-ts), and Go library (edictum-go).

## Schema

The schema defines the structure for Edictum YAML rulesets (`edictum/v1` `Ruleset`), including pre/post/session/sandbox rule types, expression operators, and observability configuration.

**v2 schema** uses the new developer-friendly terminology:
- `rules:` (was `contracts:`)
- `action:` (was `effect:`)
- `action: block` (was `effect: deny`)
- `action: ask` (was `effect: approve`)
- `kind: Ruleset` (was `kind: ContractBundle`)

The v1 schema remains for backward compatibility during the transition period.

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
