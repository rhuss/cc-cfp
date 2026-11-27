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

Store not accessible (the store resolved, but `os.stat` of `<store>/config.md` fails with an error other than "not found", for example folder permissions or a symlink loop): the same shape, with `<store-error>cannot access /abs/store/config.md: Permission denied</store-error>`. A store or `config.md` that does not exist is not an error; it gives `<store-initialized>false</store-initialized>`.

The hook exits 0 in all cases. Skills (preamble Step 0): when `<store-error>` is present, show it and stop, with a hint to fix the variable it names or to check the named path; do not offer `/cfp:init`.
