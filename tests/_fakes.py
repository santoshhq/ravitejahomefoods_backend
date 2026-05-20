import fnmatch
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from bson import ObjectId


@dataclass
class InsertOneResult:
    inserted_id: ObjectId


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int


@dataclass
class DeleteResult:
    deleted_count: int


class FakeCursor:
    def __init__(self, items: Iterable[dict]):
        self._items = list(items)
        self._skip = 0
        self._limit: Optional[int] = None

    def sort(self, key: str, direction: int):
        reverse = direction < 0
        self._items.sort(key=lambda item: item.get(key), reverse=reverse)
        return self

    def skip(self, count: int):
        self._skip = count
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    async def to_list(self, length: Optional[int] = None):
        items = self._items[self._skip :]
        if self._limit is not None:
            items = items[: self._limit]
        if length is not None:
            items = items[:length]
        return [deepcopy(item) for item in items]


class FakeCollection:
    def __init__(self, initial: Optional[list[dict]] = None):
        self._docs: list[dict] = []
        if initial:
            for doc in initial:
                self._docs.append(self._prepare_doc(doc))

    def insert_one_sync(self, doc: dict) -> dict:
        prepared = self._prepare_doc(doc)
        self._docs.append(prepared)
        return prepared

    def _prepare_doc(self, doc: dict) -> dict:
        prepared = deepcopy(doc)
        if "_id" not in prepared:
            prepared["_id"] = ObjectId()
        return prepared

    def _match_value(self, doc_value: Any, expected: Any) -> bool:
        if isinstance(expected, dict):
            if "$regex" in expected:
                pattern = expected.get("$regex", "")
                options = expected.get("$options", "")
                flags = re.IGNORECASE if "i" in options else 0
                return re.search(pattern, str(doc_value or ""), flags) is not None
            if "$gte" in expected or "$lt" in expected:
                if "$gte" in expected and (doc_value is None or doc_value < expected["$gte"]):
                    return False
                if "$lt" in expected and (doc_value is None or doc_value >= expected["$lt"]):
                    return False
                return True
            if "$elemMatch" in expected:
                if not isinstance(doc_value, list):
                    return False
                return any(self._match_dict(item, expected["$elemMatch"]) for item in doc_value)
        return doc_value == expected

    def _match_dotted_list(self, doc: dict, prefix: str, constraints: dict) -> bool:
        items = doc.get(prefix, [])
        if not isinstance(items, list):
            return False
        for item in items:
            if self._match_dict(item, constraints):
                return True
        return False

    def _match_dict(self, doc: dict, query: dict) -> bool:
        list_constraints: dict[str, dict] = {}
        for key, expected in query.items():
            if "." in key:
                prefix, subkey = key.split(".", 1)
                list_constraints.setdefault(prefix, {})[subkey] = expected
            else:
                if not self._match_value(doc.get(key), expected):
                    return False

        for prefix, constraints in list_constraints.items():
            if not self._match_dotted_list(doc, prefix, constraints):
                return False

        return True

    def _find_one(self, query: dict) -> Optional[dict]:
        for doc in self._docs:
            if self._match_dict(doc, query):
                return doc
        return None

    async def insert_one(self, doc: dict) -> InsertOneResult:
        prepared = self._prepare_doc(doc)
        self._docs.append(prepared)
        return InsertOneResult(inserted_id=prepared["_id"])

    async def find_one(self, query: dict) -> Optional[dict]:
        doc = self._find_one(query)
        return deepcopy(doc) if doc else None

    def find(self, query: dict) -> FakeCursor:
        matches = [doc for doc in self._docs if self._match_dict(doc, query)]
        return FakeCursor(matches)

    async def find_one_and_update(self, query: dict, update: dict, return_document: Any = None):
        doc = self._find_one(query)
        if not doc:
            return None
        self._apply_update(doc, query, update)
        return deepcopy(doc)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> UpdateResult:
        doc = self._find_one(query)
        if not doc:
            if not upsert:
                return UpdateResult(matched_count=0, modified_count=0)
            doc = {}
            for key, value in query.items():
                if key.startswith("$") or "." in key:
                    continue
                doc[key] = value
            if "$setOnInsert" in update:
                doc.update(update["$setOnInsert"])
            if "$set" in update:
                doc.update(update["$set"])
            if "$push" in update:
                for field, value in update["$push"].items():
                    doc.setdefault(field, []).append(value)
            self._docs.append(self._prepare_doc(doc))
            return UpdateResult(matched_count=1, modified_count=1)

        before = deepcopy(doc)
        self._apply_update(doc, query, update)
        modified = 1 if doc != before else 0
        return UpdateResult(matched_count=1, modified_count=modified)

    async def delete_one(self, query: dict) -> DeleteResult:
        for idx, doc in enumerate(self._docs):
            if self._match_dict(doc, query):
                del self._docs[idx]
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    async def delete_many(self, query: dict) -> DeleteResult:
        to_delete = [doc for doc in self._docs if self._match_dict(doc, query)]
        deleted = len(to_delete)
        self._docs = [doc for doc in self._docs if doc not in to_delete]
        return DeleteResult(deleted_count=deleted)

    async def count_documents(self, query: dict) -> int:
        return len([doc for doc in self._docs if self._match_dict(doc, query)])

    async def distinct(self, field: str):
        values = set()
        for doc in self._docs:
            if field in doc:
                values.add(doc[field])
        return list(values)

    def aggregate(self, pipeline: list[dict]) -> FakeCursor:
        return FakeCursor([])

    def _apply_update(self, doc: dict, query: dict, update: dict) -> None:
        if "$set" in update:
            for key, value in update["$set"].items():
                if key.startswith("items.$."):
                    self._apply_items_positional(doc, query, key, value, op="set")
                else:
                    doc[key] = value
        if "$inc" in update:
            for key, value in update["$inc"].items():
                if key.startswith("items.$."):
                    self._apply_items_positional(doc, query, key, value, op="inc")
                else:
                    doc[key] = (doc.get(key) or 0) + value
        if "$push" in update:
            for field, value in update["$push"].items():
                doc.setdefault(field, []).append(value)
        if "$pull" in update:
            for field, value in update["$pull"].items():
                if field not in doc or not isinstance(doc[field], list):
                    continue
                remaining = []
                for item in doc[field]:
                    if not self._match_dict(item, value):
                        remaining.append(item)
                doc[field] = remaining

    def _apply_items_positional(self, doc: dict, query: dict, key: str, value: Any, op: str) -> None:
        field = key.split("items.$.", 1)[-1]
        constraints = {}
        for qkey, qvalue in query.items():
            if qkey.startswith("items."):
                subkey = qkey.split("items.", 1)[-1]
                constraints[subkey] = qvalue
        for item in doc.get("items", []):
            if self._match_dict(item, constraints):
                if op == "inc":
                    item[field] = (item.get(field) or 0) + value
                else:
                    item[field] = value
                break


class FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def scan_iter(self, pattern: str):
        for key in list(self._store.keys()):
            if fnmatch.fnmatch(key, pattern):
                yield key

    async def ping(self):
        return True

    async def close(self):
        return True


class FakeS3:
    def __init__(self):
        self._keys: set[str] = set()

    def upload_fileobj(self, fileobj, bucket: str, key: str, ExtraArgs: Optional[dict] = None):
        self._keys.add(key)

    def list_objects_v2(self, Bucket: str, Prefix: str):
        keys = [key for key in self._keys if key.startswith(Prefix)]
        return {"Contents": [{"Key": key} for key in sorted(keys)]}

    def delete_object(self, Bucket: str, Key: str):
        self._keys.discard(Key)


class FakeRazorpayUtility:
    def verify_payment_signature(self, payload: dict):
        return True


class FakeRazorpayOrder:
    def __init__(self, order_id: str = "order_test_1"):
        self._order_id = order_id

    def create(self, payload: dict):
        return {"id": self._order_id}


class FakeRazorpayClient:
    def __init__(self):
        self.order = FakeRazorpayOrder()
        self.utility = FakeRazorpayUtility()
