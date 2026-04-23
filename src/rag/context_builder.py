from typing import List

from src.core.models import RetrievalResult
from src.core.context_models import BuiltContext


class ContextBuilder:
    def build(self, retrieval_results: List[RetrievalResult]) -> BuiltContext:
        context_text = self._build_context_text(retrieval_results)
        return BuiltContext(
            context_text=context_text,
            results_used=retrieval_results,
            total_chars=len(context_text)
        )

    def _build_context_text(self, retrieval_results: List[RetrievalResult]) -> str:
        domain = []
        subdomain = []
        product = []
        cross_doc = []

        for result in retrieval_results:
            content = result.chunk.content.strip()

            if not content:
                continue

            if result.chunk.type == "domain":
                domain.append(content)
            elif result.chunk.type == "subdomain":
                subdomain.append(content)
            elif result.chunk.type == "product":
                product.append(content)
            elif result.chunk.type == "cross_doc":
                cross_doc.append(content)

        domain = list(dict.fromkeys(domain))
        subdomain = list(dict.fromkeys(subdomain))
        product = list(dict.fromkeys(product))
        cross_doc = list(dict.fromkeys(cross_doc))

        parts = ["RETRIEVED CONTEXT"]
        for section_text in [
            self._build_text_section(cross_doc, "CROSS_DOC"),
            self._build_text_section(product, "PRODUCT"),
            self._build_text_section(subdomain, "SUBDOMAIN"),
            self._build_text_section(domain, "DOMAIN"),
        ]:
            if section_text:
                parts.append(section_text)

        return "\n\n".join(parts)

    def _build_text_section(self, section_list: List[str], section_type: str) -> str:
        if not section_list:
            return ""
        return f"{section_type}\n" + "\n\n".join(section_list)
