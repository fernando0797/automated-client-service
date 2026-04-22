from dataclasses import dataclass


@dataclass
class Ticket:
    description: str
    ticket_id: str | None = None
    source: str | None = None
    domain: str | None = None
    subdomain: str | None = None
    product: str | None = None
