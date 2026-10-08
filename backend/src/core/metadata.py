from typing import Any


# KNOWLEDGE DOCUMENT VALIDATION

REQUIRED_KNOWLEDGE_DOCUMENT_METADATA_FIELDS = {
    "domain": {"domain", "type"},
    "subdomain": {"domain", "subdomain", "type"},
    "product": {"product", "type"},
    "cross_doc": {"domain", "subdomain", "product", "type"}
}

VALID_DOCUMENT_TYPES = set(REQUIRED_KNOWLEDGE_DOCUMENT_METADATA_FIELDS.keys())


def validate_knowledge_document_metadata(metadata: dict[str, Any]) -> None:
    doc_type = metadata.get("type")

    if doc_type is None:
        raise ValueError("Metadata is missing required field: 'type'.")

    if doc_type not in VALID_DOCUMENT_TYPES:
        raise ValueError(
            f"Invalid document type '{doc_type}'."
            f"Expected one of: {sorted(VALID_DOCUMENT_TYPES)}."
        )

    required_fields = REQUIRED_KNOWLEDGE_DOCUMENT_METADATA_FIELDS[doc_type]
    missing_fields = [
        field for field in required_fields if field not in metadata]

    if missing_fields:
        raise ValueError(
            f"Metadata for type '{doc_type}' is missing required fields: {missing_fields}"
        )


# KNOWLEDGE CHUNK VALIDATION
REQUIRED_KNOWLEDGE_CHUNK_METADATA_FIELDS = {
    "parent_doc_id", "chunk_index", "chunk_id"}


def validate_knowledge_chunk_metadata(metadata: dict[str, Any]) -> None:
    validate_knowledge_document_metadata(metadata)

    missing_fields = [
        field for field in REQUIRED_KNOWLEDGE_CHUNK_METADATA_FIELDS if field not in metadata]

    if missing_fields:
        raise ValueError(
            f"Chunk metadata is missing required fields: {missing_fields}"
        )
