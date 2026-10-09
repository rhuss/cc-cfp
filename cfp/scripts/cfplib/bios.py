"""Bio variations and speaker resources."""

from cfplib import CfpError, store, text as textutil

RESOURCE_TYPES = ("recording", "repository", "blog", "session", "publication", "other")


# ---------------------------------------------------------------- bios


def _bio_summary(meta, body):
    return {
        "name": meta.get("name"),
        "emphasis": meta.get("emphasis", ""),
        "target_length": meta.get("target_length"),
        "chars": textutil.count_chars(body),
        "updated": meta.get("updated"),
    }


def write_bio(store_path, name, emphasis, target_length, text, today=None):
    path = store.bio_path(store_path, name)
    if path.is_file():
        meta, _ = store.load(path)
    else:
        meta = {"name": name, "emphasis": "", "target_length": None, "updated": None, "chars": 0}
    meta["name"] = name
    if emphasis is not None:
        meta["emphasis"] = emphasis
    if target_length is not None:
        try:
            meta["target_length"] = int(target_length)
        except (TypeError, ValueError):
            raise CfpError(f"target length must be an integer, got {target_length!r}")
    body = textutil.normalize(text)
    meta["chars"] = textutil.count_chars(body)
    meta["updated"] = textutil.today_iso(today)
    store.save(path, meta, body + "\n" if body else "")
    return {"path": str(path), "chars": meta["chars"]}


def list_bios(store_path):
    items, problems = store.list_dir(store_path, "bios")
    listing = []
    for path, meta, body in items:
        summary = _bio_summary(meta, body)
        summary["name"] = summary["name"] or path.stem
        listing.append(summary)
    return listing, problems


def show_bio(store_path, name):
    path = store.bio_path(store_path, name)
    if not path.is_file():
        raise CfpError(f"unknown bio '{name}'")
    meta, body = store.load(path)
    result = _bio_summary(meta, body)
    result["name"] = name
    result["text"] = textutil.normalize(body)
    return result


def delete_bio(store_path, name):
    path = store.bio_path(store_path, name)
    if not path.is_file():
        raise CfpError(f"unknown bio '{name}'")
    path.unlink()
    return {"deleted": str(path)}


# ---------------------------------------------------------------- resources


def _resource_summary(meta, path):
    return {
        "id": meta.get("id") or path.stem,
        "type": meta.get("type", ""),
        "title": meta.get("title", ""),
        "link": meta.get("link", ""),
        "date": meta.get("date"),
        "notes": meta.get("notes") or "",
    }


def write_resource(store_path, data):
    data = dict(data or {})
    title = str(data.get("title") or "").strip()
    if not title:
        raise CfpError("resource needs a title")
    kind = str(data.get("type") or "").strip()
    if kind not in RESOURCE_TYPES:
        raise CfpError(f"resource type must be one of {', '.join(RESOURCE_TYPES)}, got {kind!r}")
    link = str(data.get("link") or "").strip()
    if not link:
        raise CfpError("resource needs a link")
    resource_id = data.get("id")
    if resource_id:
        store.check_id(resource_id, "resource id")
    else:
        resource_id = store.slugify(title, store.existing_ids(store_path, "resources"))
    path = store.resource_path(store_path, resource_id)
    if not data.get("id") and path.exists():
        raise CfpError(f"resource file {path} already exists; pass \"id\": \"{resource_id}\" to update it")
    body = ""
    if path.is_file():
        meta, body = store.load(path)
    else:
        meta = {}
    meta.update(
        {
            "id": resource_id,
            "type": kind,
            "title": title,
            "link": link,
            "date": data.get("date") or None,
            "notes": data.get("notes") or "",
        }
    )
    if data.get("description"):
        body = textutil.normalize(data["description"]) + "\n"
    store.save(path, meta, body)
    return {"path": str(path), "id": resource_id}


def list_resources(store_path, kind=None):
    items, problems = store.list_dir(store_path, "resources")
    listing = [_resource_summary(meta, path) for path, meta, _ in items]
    if kind:
        listing = [r for r in listing if r["type"] == kind]
    return listing, problems


def load_resource(store_path, resource_id):
    path = store.resource_path(store_path, resource_id)
    if not path.is_file():
        raise CfpError(f"unknown resource '{resource_id}'")
    meta, _ = store.load(path)
    return _resource_summary(meta, path)


def delete_resource(store_path, resource_id):
    path = store.resource_path(store_path, resource_id)
    if not path.is_file():
        raise CfpError(f"unknown resource '{resource_id}'")
    path.unlink()
    return {"deleted": str(path)}
