# AIL Spec

Canonical language file remains `/AIL.md` (version 1.1).

Required fields for a valid platform message:
- @from
- @to
- @intent
- @id
- @lang

Optional:
- @ref

Versioning:
- ail/1.0 historical
- ail/1.1 current
- ail/1.2+ additive fields only
- ail/2.0 may break; readers ignore unknown fields in 1.x
