# Simplified metadata parser limitations

The portfolio validator deliberately uses a small YAML-like front-matter parser and has no YAML dependency.

Supported:

- one `key: value` pair per line;
- quoted or unquoted scalar strings;
- `null`, `~`, booleans and simple numeric literals;
- one-line lists such as `[DIM-0001, DIM-0002]`.

Not supported:

- nested mappings or indentation-based lists;
- multiline scalars (`|` or `>`);
- anchors, aliases, tags and merge keys;
- inline mappings, complex quoting/escaping and comments after values;
- YAML date coercion or full YAML 1.2 semantics.

Unsupported syntax must fail validation rather than be silently interpreted. A production implementation should use a maintained YAML parser, a versioned JSON Schema and explicit schema migration rules.
