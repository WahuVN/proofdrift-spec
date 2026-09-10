#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const schemaDir = path.join(root, "contracts", "schemas");

const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
  validateFormats: false,
});

const validators = new Map();
for (const name of fs.readdirSync(schemaDir).filter((entry) => entry.endsWith(".schema.json")).sort()) {
  const document = JSON.parse(fs.readFileSync(path.join(schemaDir, name), "utf8"));
  ajv.addSchema(document);
}
for (const name of fs.readdirSync(schemaDir).filter((entry) => entry.endsWith(".schema.json")).sort()) {
  const schemaName = name.slice(0, -".schema.json".length);
  const document = JSON.parse(fs.readFileSync(path.join(schemaDir, name), "utf8"));
  const validator = ajv.getSchema(document.$id);
  if (!validator) {
    throw new Error(`Ajv did not register schema ${schemaName} (${document.$id})`);
  }
  validators.set(schemaName, validator);
}

const inputPath = process.argv[2];
if (!inputPath) {
  console.error("usage: node contracts/tools/conformance_ajv.mjs <vectors.jsonl>");
  process.exit(2);
}

const rows = fs.readFileSync(inputPath, "utf8").split(/\r?\n/).filter((line) => line.trim());
const seen = new Set();
for (let index = 0; index < rows.length; index += 1) {
  const vector = JSON.parse(rows[index]);
  if (typeof vector.vector_id !== "string" || typeof vector.schema !== "string" || !("document" in vector)) {
    throw new Error(`line ${index + 1}: malformed conformance vector`);
  }
  if (seen.has(vector.vector_id)) {
    throw new Error(`line ${index + 1}: duplicate vector_id ${vector.vector_id}`);
  }
  seen.add(vector.vector_id);
  const validate = validators.get(vector.schema);
  if (!validate) {
    throw new Error(`line ${index + 1}: unknown schema ${vector.schema}`);
  }
  const accepted = Boolean(validate(vector.document));
  process.stdout.write(`${JSON.stringify({ vector_id: vector.vector_id, accepted })}\n`);
}
