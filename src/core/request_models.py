from pydantic import BaseModel


class Ticket(BaseModel):
    ticket_id: str | None = None
    source: str | None = None
    description: str
    domain: str
    subdomain: str
    product: str
