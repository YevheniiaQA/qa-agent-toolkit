"""qa_schema — the JSON Schema subset the toolkit's schemas use, with no third-party dependency.

Supported keywords: type, enum, const, required, properties, additionalProperties,
patternProperties, items, minItems, minLength, minimum, pattern, anyOf, $ref (local "#/$defs/...").
Anything else in a schema is ignored, so keep schemas inside this subset.

  validate(instance, schema) -> list of "path: message" strings, empty when valid
  load(name)                 -> schema dict from ../schemas/<name>.schema.json
"""
import json, os, re

SCHEMAS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "schemas")
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
MAX_ERRORS = 50


def load(name):
    with open(os.path.join(SCHEMAS, f"{name}.schema.json"), encoding="utf-8") as fh:
        return json.load(fh)


def names():
    return sorted(f[:-len(".schema.json")] for f in os.listdir(SCHEMAS) if f.endswith(".schema.json"))


def _is_type(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[t])


def validate(instance, schema, root=None, path="$", errors=None):
    root = schema if root is None else root
    errors = [] if errors is None else errors
    if len(errors) >= MAX_ERRORS:
        return errors
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"unsupported $ref {ref}")
        return validate(instance, root["$defs"][ref[len("#/$defs/"):]], root, path, errors)
    if "anyOf" in schema:
        if not any(not validate(instance, s, root, path, []) for s in schema["anyOf"]):
            errors.append(f"{path}: matches none of the allowed shapes")
            return errors
    t = schema.get("type")
    if t is not None:
        allowed = t if isinstance(t, list) else [t]
        if not any(_is_type(instance, x) for x in allowed):
            errors.append(f"{path}: expected {' or '.join(allowed)}, got {type(instance).__name__}")
            return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: must be {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than {schema['minLength']} characters")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool) and "minimum" in schema:
        if instance < schema["minimum"]:
            errors.append(f"{path}: below {schema['minimum']}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(instance):
                validate(item, schema["items"], root, f"{path}[{i}]", errors)
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required field '{key}'")
        props, pats = schema.get("properties", {}), schema.get("patternProperties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in instance.items():
            sub = f"{path}.{key}"
            if key in props:
                validate(value, props[key], root, sub, errors)
                continue
            matched = [s for p, s in pats.items() if re.search(p, key)]
            for s in matched:
                validate(value, s, root, sub, errors)
            if not matched:
                if extra is False:
                    errors.append(f"{path}: unexpected field '{key}'")
                elif isinstance(extra, dict):
                    validate(value, extra, root, sub, errors)
    return errors
