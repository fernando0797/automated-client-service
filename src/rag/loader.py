from __future__ import annotations

import json
import re
from pathlib import Path

from src.core.metadata import validate_knowledge_document_metadata
from src.core.models import KnowledgeDocument


class KnowledgeLoader:
    def __init__(self, knowledge_base_path: str | Path) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)

    def load_all_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []

        target_folders = ["domains", "subdomains", "products", "cross"]

        for folder_name in target_folders:
            folder_path = self.knowledge_base_path / folder_name

            if not folder_path.exists():
                continue

            for file_path in sorted(folder_path.rglob("*.md")):
                document = self.load_markdown_file(file_path)
                documents.append(document)

        return documents

    def load_markdown_file(self, file_path: str | Path) -> KnowledgeDocument:
        file_path = Path(file_path)
        raw_text = file_path.read_text(encoding="utf-8")

        title = self._extract_title(raw_text)
        metadata = self._extract_metadata(raw_text)
        content = self._remove_metadata_block(raw_text).strip()

        validate_knowledge_document_metadata(metadata)

        doc_id = self._build_doc_id(file_path, metadata)

        enriched_metadata = {
            **metadata,
            "source": str(file_path.as_posix()),
            "title": title,
            "filename": file_path.name,
        }

        return KnowledgeDocument(
            doc_id=doc_id,
            content=content,
            metadata=enriched_metadata,
        )

    def _extract_title(self, raw_text: str) -> str:
        match = re.search(r"^#\s+(.+)$", raw_text, re.MULTILINE)

        if match is None:
            raise ValueError(
                "Markdown document is missing a top-level title ('# ...').")

        return match.group(1).strip()

    def _extract_metadata(self, raw_text: str) -> dict:
        pattern = r"## Metadata\s*(?:```json|json)?\s*(\{.*?\})\s*(?:```)?"
        match = re.search(pattern, raw_text, re.DOTALL)

        if match is None:
            raise ValueError(
                "Markdown document is missing a valid '## Metadata' section.")

        metadata_str = match.group(1).strip()

        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in metadata block: {exc}") from exc

        return metadata

    def _remove_metadata_block(self, raw_text: str) -> str:
        pattern = r"## Metadata\s*(?:```json|json)?\s*(\{.*?\})\s*(?:```)?"
        cleaned_text = re.sub(pattern, "", raw_text, count=1, flags=re.DOTALL)
        return cleaned_text.strip()

    def _build_doc_id(self, file_path: Path, metadata: dict) -> str:
        doc_type = metadata["type"]

        if doc_type == "domain":
            return f"domain__{metadata['domain']}"

        if doc_type == "subdomain":
            return f"subdomain__{metadata['subdomain']}"

        if doc_type == "product":
            return f"product__{metadata['product']}"

        if doc_type == "cross_doc":
            return f"cross__{metadata['subdomain']}__{metadata['product']}"

        raise ValueError(
            f"Unsupported document type in file {file_path}: {doc_type}")
