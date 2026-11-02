# Proposed automation design

The historical project contained requirements for future validation, not an implementation.

The new portfolio validator demonstrates a minimal architecture:

`Markdown front matter → parser → structural rules → reference graph → JSON report → CI exit code`

Future production work would need a real YAML parser, a versioned schema, link validation, template compatibility rules, lifecycle transition checks, changed-file review and an approved publication process. It would also need decisions about owner privacy and the authoritative repository.

The demonstration intentionally avoids publishing to Confluence or any external system.

