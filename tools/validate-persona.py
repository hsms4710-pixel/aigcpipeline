#!/usr/bin/env python3
"""校验人设卡 persona.json（对照 persona-schema.json）。用法：python validate-persona.py <persona.json>"""
import json, sys, os
import jsonschema

def main():
    if len(sys.argv) < 2:
        print("用法: python validate-persona.py <persona.json>"); sys.exit(2)
    p = sys.argv[1]
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "spec", "p1-character-voice", "contracts", "persona-schema.json")
    with open(p, encoding="utf-8-sig") as f:
        data = json.load(f)
    with open(schema_path, encoding="utf-8-sig") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(data, schema)
        print(f"OK: {p} 通过 persona-schema-v0 校验")
        return 0
    except jsonschema.ValidationError as e:
        print(f"FAIL: {p}")
        print(f"  - {e.message} (at {list(e.absolute_path)})")
        return 1

if __name__ == "__main__":
    sys.exit(main())

