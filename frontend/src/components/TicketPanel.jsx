function StatusBadge({ status }) {
  const map = {
    active: { cls: "bg-green-100 text-green-700", label: "Active" },
    escalated: { cls: "bg-orange-100 text-orange-700", label: "Escalated" },
    closed: { cls: "bg-gray-200 text-gray-700", label: "Closed" },
  };
  const s = map[status] || { cls: "bg-gray-100 text-gray-600", label: status || "—" };
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border py-2.5 last:border-0">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="text-sm text-foreground">{children}</span>
    </div>
  );
}

export function TicketPanel({ ticketId, domainLabel, subdomainLabel, productLabel, meta }) {
  return (
    <aside className="w-72 shrink-0 rounded-2xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-foreground">Ticket</h3>
      <p className="mt-0.5 text-xs text-muted-foreground">#{ticketId.slice(0, 8)}</p>

      <div className="mt-3">
        <Row label="Request type">{domainLabel}</Row>
        <Row label="Reason">{subdomainLabel}</Row>
        <Row label="Product">{productLabel}</Row>
        <Row label="Status">
          <StatusBadge status={meta.status} />
        </Row>
        <Row label="RAG used">{meta.retrieval_used == null ? "—" : meta.retrieval_used ? "Yes" : "No"}</Row>
        <Row label="RAG mode">{meta.retrieval_mode || "—"}</Row>
        <Row label="Initial route">{meta.initial_route || "—"}</Row>
        {meta.nodes_executed && meta.nodes_executed.length > 0 && (
          <Row label="Nodes executed">
            <span className="text-xs text-muted-foreground">
              {meta.nodes_executed.join(" → ")}
            </span>
          </Row>
        )}
      </div>
    </aside>
  );
}
