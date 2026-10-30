// Compile each JSON Schema with Ajv's draft 2020-12 class and fail on any error.
//
// Replaces `ajv-cli@5.0.0 compile -s <file> --spec=draft2020`, which pulled in
// fast-json-patch 2.x (GHSA-8gh8-hqwg-xf34) with no fixed release in range.
// It mirrors what that command did: one Ajv2020 instance per schema with
// Ajv's default options (strict mode on), the draft-06 meta-schema added, and
// the schema added by its $id (or by file path when it has none).
//
// Usage: node scripts/validate_schemas.mjs <schema.json> [<schema.json> ...]

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

import Ajv2020 from "ajv/dist/2020.js";

const require = createRequire(import.meta.url);
const draft6MetaSchema = require("ajv/lib/refs/json-schema-draft-06.json");

function errorMessage(err) {
  try {
    return err instanceof Error ? err.message : String(err);
  } catch {
    return "unprintable error";
  }
}

function compileSchema(file) {
  try {
    const schema = JSON.parse(readFileSync(file, "utf8"));
    const ajv = new Ajv2020();
    ajv.addMetaSchema(draft6MetaSchema);
    const id = schema?.$id;
    ajv.addSchema(schema, id ? undefined : file);
    if (typeof ajv.getSchema(id || file) !== "function") {
      throw new Error("schema did not compile to a validator");
    }
    console.log(`schema ${file} is valid`);
    return true;
  } catch (err) {
    console.error(`schema ${file} is invalid`);
    console.error(`error: ${errorMessage(err)}`);
    return false;
  }
}

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error("usage: node scripts/validate_schemas.mjs <schema.json> [...]");
  process.exit(2);
}

// Compile every file before exiting so one run reports all broken schemas.
const results = files.map(compileSchema);
process.exit(results.every(Boolean) ? 0 : 1);
