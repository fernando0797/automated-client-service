import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

export function ChatMessage({ role, content }) {
  const isUser = role === "user";
  const [displayedContent, setDisplayedContent] = useState(
    isUser ? content : ""
  );

  useEffect(() => {
    if (isUser) {
      setDisplayedContent(content);
      return;
    }

    setDisplayedContent("");

    let index = 0;

    const interval = setInterval(() => {
      index += 1;
      setDisplayedContent(content.slice(0, index));

      if (index >= content.length) {
        clearInterval(interval);
      }
    }, 12);

    return () => clearInterval(interval);
  }, [content, isUser]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[75%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-sm"
            : "max-w-[75%] rounded-2xl rounded-bl-sm border border-border bg-card px-4 py-2.5 text-sm text-foreground shadow-sm"
        }
      >
        {isUser ? (
          displayedContent
        ) : (
          <div className="leading-7 [&_p]:mb-4 [&_ol]:mb-4 [&_ul]:mb-4 [&_li]:mb-2 [&_strong]:font-semibold">
            <ReactMarkdown>{displayedContent}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}