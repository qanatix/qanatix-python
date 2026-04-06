"""Ingest resource — batch, file upload, DataFrame, status."""

from __future__ import annotations

from typing import Any

from .client import CHUNK_SIZE
from .types import IngestionResult, UploadSummary, UploadError


def _to_result(data: dict) -> IngestionResult:
    summary = data.get("summary", {})
    errors = data.get("errors", [])
    return IngestionResult(
        upload_id=data.get("upload_id", ""),
        status=data.get("status", ""),
        summary=UploadSummary(
            submitted=summary.get("submitted", 0),
            accepted=summary.get("accepted", 0),
            rejected=summary.get("rejected", 0),
            dedup_skipped=summary.get("dedup_skipped", 0),
        ),
        errors=[
            UploadError(
                row=e.get("row"),
                field=e.get("field"),
                error_type=e.get("error_type"),
                message=e.get("message", ""),
            )
            for e in errors
        ],
        metadata=data.get("metadata", {}),
    )


class Ingest:
    """Synchronous ingest resource."""

    def __init__(self, http):
        self._http = http
        self._batch = f"{http.api_prefix}/ingest/batch"
        self._upload = f"{http.api_prefix}/ingest/upload"
        self._uploads = f"{http.api_prefix}/uploads"

    def batch(
        self,
        collection: str,
        record_type: str,
        records: list[dict[str, Any]],
    ) -> IngestionResult:
        """Ingest a batch of records. Auto-chunks if > 5000."""
        if len(records) <= CHUNK_SIZE:
            data = self._http.request(
                "POST", f"{self._batch}/{collection}/{record_type}", json=records,
            )
            return _to_result(data)

        # Auto-chunk
        total_accepted = 0
        total_rejected = 0
        total_submitted = 0
        all_errors: list[UploadError] = []
        last_upload_id = ""
        last_status = ""

        for i in range(0, len(records), CHUNK_SIZE):
            chunk = records[i : i + CHUNK_SIZE]
            data = self._http.request(
                "POST", f"{self._batch}/{collection}/{record_type}", json=chunk,
            )
            result = _to_result(data)
            total_submitted += result.summary.submitted
            total_accepted += result.summary.accepted
            total_rejected += result.summary.rejected
            all_errors.extend(result.errors)
            last_upload_id = result.upload_id
            last_status = result.status

        return IngestionResult(
            upload_id=last_upload_id,
            status=last_status,
            summary=UploadSummary(
                submitted=total_submitted,
                accepted=total_accepted,
                rejected=total_rejected,
            ),
            errors=all_errors,
        )

    def upload(
        self,
        collection: str,
        record_type: str,
        file_path: str,
        *,
        content_type: str | None = None,
    ) -> IngestionResult:
        """Upload a file (CSV, JSON, NDJSON, XML)."""
        import os
        filename = os.path.basename(file_path)
        ct = content_type or _guess_content_type(filename)
        with open(file_path, "rb") as f:
            file_data = f.read()
        data = self._http.upload(
            f"{self._upload}/{collection}/{record_type}", file_data, filename, ct,
        )
        return _to_result(data)

    def status(self, upload_id: str) -> dict[str, Any]:
        return self._http.request("GET", f"{self._uploads}/{upload_id}")

    def errors(self, upload_id: str) -> list[dict[str, Any]]:
        resp = self._http.request("GET", f"{self._uploads}/{upload_id}/dlq")
        return resp if isinstance(resp, list) else resp.get("entries", [])

    def from_dataframe(
        self,
        collection: str,
        record_type: str,
        df: Any,
        *,
        name_column: str = "name",
    ) -> IngestionResult:
        """Ingest records from a pandas DataFrame."""
        records = []
        for _, row in df.iterrows():
            rec = row.to_dict()
            name = rec.pop(name_column, str(row.name))
            rec = {k: v for k, v in rec.items() if v is not None and v == v}  # drop NaN
            records.append({"name": name, **rec})
        return self.batch(collection, record_type, records)


class AsyncIngest:
    """Async ingest resource."""

    def __init__(self, http):
        self._http = http
        self._batch = f"{http.api_prefix}/ingest/batch"
        self._upload = f"{http.api_prefix}/ingest/upload"
        self._uploads = f"{http.api_prefix}/uploads"

    async def batch(
        self,
        collection: str,
        record_type: str,
        records: list[dict[str, Any]],
    ) -> IngestionResult:
        if len(records) <= CHUNK_SIZE:
            data = await self._http.request(
                "POST", f"{self._batch}/{collection}/{record_type}", json=records,
            )
            return _to_result(data)

        total_accepted = 0
        total_rejected = 0
        total_submitted = 0
        all_errors: list[UploadError] = []
        last_upload_id = ""
        last_status = ""

        for i in range(0, len(records), CHUNK_SIZE):
            chunk = records[i : i + CHUNK_SIZE]
            data = await self._http.request(
                "POST", f"{self._batch}/{collection}/{record_type}", json=chunk,
            )
            result = _to_result(data)
            total_submitted += result.summary.submitted
            total_accepted += result.summary.accepted
            total_rejected += result.summary.rejected
            all_errors.extend(result.errors)
            last_upload_id = result.upload_id
            last_status = result.status

        return IngestionResult(
            upload_id=last_upload_id,
            status=last_status,
            summary=UploadSummary(
                submitted=total_submitted,
                accepted=total_accepted,
                rejected=total_rejected,
            ),
            errors=all_errors,
        )

    async def upload(
        self,
        collection: str,
        record_type: str,
        file_path: str,
        *,
        content_type: str | None = None,
    ) -> IngestionResult:
        import os
        filename = os.path.basename(file_path)
        ct = content_type or _guess_content_type(filename)
        with open(file_path, "rb") as f:
            file_data = f.read()
        data = await self._http.upload(
            f"{self._upload}/{collection}/{record_type}", file_data, filename, ct,
        )
        return _to_result(data)

    async def status(self, upload_id: str) -> dict[str, Any]:
        return await self._http.request("GET", f"{self._uploads}/{upload_id}")

    async def errors(self, upload_id: str) -> list[dict[str, Any]]:
        resp = await self._http.request("GET", f"{self._uploads}/{upload_id}/dlq")
        return resp if isinstance(resp, list) else resp.get("entries", [])

    async def from_dataframe(
        self,
        collection: str,
        record_type: str,
        df: Any,
        *,
        name_column: str = "name",
    ) -> IngestionResult:
        records = []
        for _, row in df.iterrows():
            rec = row.to_dict()
            name = rec.pop(name_column, str(row.name))
            rec = {k: v for k, v in rec.items() if v is not None and v == v}
            records.append({"name": name, **rec})
        return await self.batch(collection, record_type, records)


def _guess_content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "csv": "text/csv",
        "json": "application/json",
        "ndjson": "application/x-ndjson",
        "xml": "application/xml",
    }.get(ext, "application/octet-stream")
