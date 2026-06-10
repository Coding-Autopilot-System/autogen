# Enterprise Audit-Fix Classification

Source: `gsd-audit-fix --severity all --max 8`

| ID | Severity | Classification | Finding |
|---|---|---|---|
| F-01 | High | Auto-fixable | Clean clone could not collect the shipped full test suite because required runtime modules and dependency/bootstrap files were missing. |
| F-02 | High | Auto-fixable | CI ran only two static contract tests and could report green while the broader suite was broken. |
| F-03 | High | Auto-fixable | `SessionStore` composed unvalidated session, stage, and attempt identifiers into filesystem paths. |
| F-04 | High | Auto-fixable | Dashboard CORS allowed wildcard origins with credentials. |
| F-05 | Medium | Auto-fixable | Repo write operations accepted arbitrary encodings and used non-atomic direct writes. |
| F-06 | Medium | Auto-fixable | Missing `.gitignore` exposed secrets and runtime/test artifacts to accidental commits. |
| F-07 | Medium | Manual-only | Legacy dashboard and MAF runtime contracts overlap and require an architectural consolidation decision. |
| F-08 | Medium | Manual-only | Production authentication, worker isolation, and remote deployment boundaries remain intentionally unimplemented. |
