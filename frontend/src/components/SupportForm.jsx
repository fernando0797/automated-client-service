import { useMemo, useState } from "react";
import { DOMAINS, PRODUCTS } from "@/data/supportOptions";

export function SupportForm({ onSubmit }) {
  const [domain, setDomain] = useState("");
  const [subdomain, setSubdomain] = useState("");
  const [product, setProduct] = useState("");

  const subdomains = useMemo(() => {
    const d = DOMAINS.find((x) => x.value === domain);
    return d ? d.subdomains : [];
  }, [domain]);

  const canContinue = domain && subdomain && product;

  const selectCls =
    "w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <div className="mx-auto w-full max-w-xl rounded-2xl border border-border bg-card p-8 shadow-sm">
      <h2 className="text-2xl font-semibold text-foreground">How can we help?</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Tell us a bit about your request so we can route you to the right assistant.
      </p>

      <div className="mt-6 space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-foreground">
            Request type
          </label>
          <select
            className={selectCls}
            value={domain}
            onChange={(e) => {
              setDomain(e.target.value);
              setSubdomain("");
            }}
          >
            <option value="">Select a request type</option>
            {DOMAINS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-foreground">
            Request reason
          </label>
          <select
            className={selectCls}
            value={subdomain}
            onChange={(e) => setSubdomain(e.target.value)}
            disabled={!domain}
          >
            <option value="">
              {domain ? "Select a reason" : "Select a request type first"}
            </option>
            {subdomains.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-foreground">
            Product
          </label>
          <select
            className={selectCls}
            value={product}
            onChange={(e) => setProduct(e.target.value)}
          >
            <option value="">Select a product</option>
            {PRODUCTS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <button
          disabled={!canContinue}
          onClick={() => onSubmit({ domain, subdomain, product })}
          className="mt-2 w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue to chat
        </button>
      </div>
    </div>
  );
}
