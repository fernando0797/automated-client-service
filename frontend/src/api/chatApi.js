export async function sendChatMessage(payload) {
  const apiUrl = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
    /\/$/,
    "",
  );
  const res = await fetch(`${apiUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json();
}
