# Rule reference — 0.1.0

All findings are static review prompts. Severity describes review priority, not
confirmed exploitation. At most one finding per rule per enabled server is
emitted. Paths are JSON pointers, not source line numbers.

| ID | Priority | Checks | Scope / possible false positives |
| --- | --- | --- | --- |
| ACA001 | High | Secret-like env/header names and CLI flags containing literal values | Does not inspect arbitrary strings/files or detect every secret; a client must actually support the placeholder syntax |
| ACA002 | Medium | Common npx/npm exec/uvx package arguments lack exact semver | Conservative for complex options and uvx --from/--with; exact versions do not prove provenance or lock transitive dependencies |
| ACA003 | High | Direct shell/interpreter launcher | Intentional wrappers may be valid; does not inspect scripts or nested launchers |
| ACA004 | High | Positional/assignment arguments naming filesystem roots, entire home directories or common home placeholders | An argument may not be a filesystem grant; relative paths, symlinks and server semantics are not resolved |
| ACA005 | High | Docker/Podman --privileged or --privileged=true | Not a complete container-hardening audit |
| ACA006 | High | Docker/Podman broad host/home mounts or engine sockets | Common -v/--volume/--mount syntax only; no Docker daemon queries or path expansion |
| ACA007 | High | HTTP endpoint outside literal loopback | No DNS/network lookup; private network HTTP also needs review |
| ACA008 | High | Common environment/argument TLS-verification bypasses | NODE_TLS_REJECT_UNAUTHORIZED, PYTHONHTTPSVERIFY, GIT_SSL_NO_VERIFY, --insecure, --ignore-certificate-errors; not every runtime |
| ACA009 | Medium | Package launch -y/--yes flags | May be intentional in reproducible automation; still inspect what will be installed |
| ACA010 | Medium | URL userinfo or secret-like query keys, decoded once for percent encoding | Values are never emitted; not all credential naming patterns are recognized |
| ACA011 | Medium | Plain HTTP literal localhost/loopback | Local HTTP is common; review authentication and origin checks separately |
| ACA012 | Medium | Invalid URL, non-HTTP(S), absent host, interpolated/unreviewable host or invalid port | A client might interpolate a supported endpoint; inspect the resolved URL yourself |

The tool reads neither referenced environment variables nor filesystem paths
inside a config. It never fixes configurations automatically. Field-level diffs
report additions/removals and changed command/args/url/env/headers/type/cwd/disabled
categories; unknown fields appear as `other`. This detects change, not whether a
permission expansion actually occurred.
