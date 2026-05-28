import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TicketPanel } from "./TicketPanel";
import { sendChatMessage } from "@/api/chatApi";
import { DOMAINS, PRODUCTS } from "@/data/supportOptions";

function uuid() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "tkt-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

export function ChatWindow({ selection, onReset }) {
  const { domain, subdomain, product } = selection;

  const domainObj = DOMAINS.find((d) => d.value === domain);
  const subdomainObj = domainObj?.subdomains.find((s) => s.value === subdomain);
  const productObj = PRODUCTS.find((p) => p.value === product);

  const [ticketId] = useState(() => uuid());
  const [turnId, setTurnId] = useState(1);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi, I’m the Fer&Vic support assistant. Describe your issue and I’ll help you step by step.",
    },
  ]);
  const [meta, setMeta] = useState({
    status: "active",
    retrieval_used: null,
    retrieval_mode: "",
    initial_route: "",
    nodes_executed: [],
  });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const scrollRef = useRef(null);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const isEscalated = meta.status === "escalated";
  const isClosed = meta.status === "closed";
  const inputDisabled = sending || isEscalated || isClosed;

  const handleSend = async (text) => {
    setError("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const data = await sendChatMessage({
        ticket_id: ticketId,
        turn_id: String(turnId),
        source: "web",
        description: text,
        domain,
        subdomain,
        product,
      });

      setMessages((m) => [...m, { role: "assistant", content: data.response }]);

      const nextStatus = data.should_close
        ? "closed"
        : data.requires_escalation
          ? "escalated"
          : data.status || "active";

      setMeta({
        status: nextStatus,
        retrieval_used: data.retrieval_used,
        retrieval_mode: data.retrieval_mode,
        initial_route: data.initial_route,
        nodes_executed: data.nodes_executed || [],
      });
      setTurnId((n) => n + 1);
    } catch (e) {
      setError(
        "Could not connect to the support service. Please check that the backend is running.",
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-1 gap-6">
      <TicketPanel
        ticketId={ticketId}
        domainLabel={domainObj?.label || domain}
        subdomainLabel={subdomainObj?.label || subdomain}
        productLabel={productObj?.label || product}
        meta={meta}
      />

      <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-5 py-3">
          <h2 className="text-base font-semibold text-foreground">Fer&amp;Vic Support</h2>
        </div>

        <div
          ref={scrollRef}
          className="flex-1 space-y-3 overflow-y-auto bg-background/40 p-5"
          style={{ minHeight: "400px", maxHeight: "60vh" }}
        >
          {messages.map((m, i) => (
            <ChatMessage key={i} role={m.role} content={m.content} />
          ))}
          {sending && (
            <ChatMessage role="assistant" content="…" />
          )}
        </div>

        {(isEscalated || isClosed || error) && (
          <div className="border-t border-border px-5 py-3">
            {isEscalated && (
              <div className="rounded-lg bg-orange-50 px-3 py-2 text-sm text-orange-700">
                Your case has been escalated to a human agent.
              </div>
            )}
            {isClosed && (
              <div className="flex items-center justify-between gap-3 rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-700">
                <span>The conversation has been closed successfully.</span>
                <button
                  onClick={onReset}
                  className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                >
                  Start new ticket
                </button>
              </div>
            )}
            {error && !isEscalated && !isClosed && (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        )}

        <ChatInput onSend={handleSend} disabled={inputDisabled} />
      </div>
    </div>
  );
}
