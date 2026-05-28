import { useState } from "react";

export function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const v = text.trim();
    if (!v || disabled) return;
    onSend(v);
    setText("");
  };

  return (
    <form
      onSubmit={submit}
      className="flex gap-2 border-t border-border bg-card p-4"
    >
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type your message..."
        disabled={disabled}
        className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Send
      </button>
    </form>
  );
}
