# Contract: `<cfp-context>`

Success:

```xml
<cfp-context>
<plugin-root>/path/to/cfp</plugin-root>
<store>/abs/store</store>
<store-initialized>true|false</store-initialized>
<today>2026-11-27</today>
</cfp-context>
```

`<store>` is the path from `paths.resolve_store(None)`, so it is never empty on success (the default store applies).

Resolution error (invalid `CFP_CONFIG_DIR`, `CFP_STORE`, or `CFP_DATA_DIR` reached as fallback):

```xml
<cfp-context>
<plugin-root>/path/to/cfp</plugin-root>
<store></store>
<store-initialized>false</store-initialized>
<store-error>CFP_STORE must be an absolute path, got 'talks'</store-error>
<today>2026-11-27</today>
</cfp-context>
```

The hook exits 0 in both cases. Skills (preamble Step 0): when `<store-error>` is present, show it with the hint to fix the variable and stop; do not offer `/cfp:init`.
