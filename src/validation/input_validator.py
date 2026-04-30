from __future__ import annotations

import json
from pathlib import Path

from src.core.request_models import Ticket


class InputValidator:
    def __init__(self, taxonomies_path: str | Path):
        self.taxonomies_path = Path(taxonomies_path)

        self.valid_domains = self._load_domains()
        self.valid_products = self._load_products()
        self.domain_to_subdomains = self._load_domain_to_subdomains()
        self.valid_subdomains = {
            subdomain
            for subdomains in self.domain_to_subdomains.values()
            for subdomain in subdomains
        }

    def validate(self, ticket: Ticket) -> Ticket:
        self._validate_non_empty_text(ticket.description, "description")

        if ticket.ticket_id is not None:
            self._validate_non_empty_text(ticket.ticket_id, "ticket_id")

        if ticket.turn_id is not None:
            self._validate_non_empty_text(ticket.turn_id, "turn_id")

        self._validate_domain(ticket.domain)
        self._validate_product(ticket.product)
        self._validate_subdomain(ticket.subdomain)
        self._validate_domain_subdomain_consistency(
            domain=ticket.domain,
            subdomain=ticket.subdomain,
        )
        return ticket

    def _load_domains(self) -> set[str]:
        data = self._load_json("domain_schema.json")
        return set(data["domains"])

    def _load_products(self) -> set[str]:
        data = self._load_json("product_catalog.json")
        return set(data["products"])

    def _load_domain_to_subdomains(self) -> dict[str, set[str]]:
        data = self._load_json("subdomain_schema.json")
        return {
            domain: set(subdomains)
            for domain, subdomains in data.items()
        }

    def _load_json(self, filename: str) -> dict:
        file_path = self.taxonomies_path / filename
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_non_empty_text(self, value: str, field_name: str) -> None:
        if not value.strip():
            raise ValueError(f"Invalid {field_name}: cannot be empty")

    def _validate_domain(self, domain: str) -> None:
        if domain not in self.valid_domains:
            raise ValueError(f"Invalid domain: {domain}")

    def _validate_product(self, product: str) -> None:
        if product not in self.valid_products:
            raise ValueError(f"Invalid product: {product}")

    def _validate_subdomain(self, subdomain: str) -> None:
        if subdomain not in self.valid_subdomains:
            raise ValueError(f"Invalid subdomain: {subdomain}")

    def _validate_domain_subdomain_consistency(
        self,
        domain: str,
        subdomain: str,
    ) -> None:
        valid_subdomains_for_domain = self.domain_to_subdomains[domain]

        if subdomain not in valid_subdomains_for_domain:
            raise ValueError(
                f"Subdomain '{subdomain}' is not valid for domain '{domain}'"
            )
