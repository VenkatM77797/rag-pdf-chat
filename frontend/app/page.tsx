"use client";

import { useState } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[] | []>([]);
  const [loading, setLoading] = useState(false);

  const askAI = async () => {
    if (!question.trim()) return;

    const userMsg = { role: "user" as const, text: question };

    setMessages((prev) => [
      ...prev,
      userMsg,
      { role: "bot" as const, text: "" },
    ]);

    const currentQuestion = question;
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/ask-stream?q=${encodeURIComponent(
          currentQuestion
        )}`
      );

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();

      let fullText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;

        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = {
            role: "bot" as const,
            text: fullText,
          };
          return copy;
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "❌ Error connecting to backend",
        },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-black text-white">

      {/* HEADER */}
      <div className="p-4 border-b border-gray-800 text-center font-bold">
        🧠 RAG Chat (Streaming + LLaMA 3)
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user"
                ? "justify-end"
                : "justify-start"
            }`}
          >
            <div
              className={`px-4 py-2 rounded-2xl max-w-[70%] whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600"
                  : "bg-gray-800"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-gray-400 text-sm">
            AI is typing...
          </div>
        )}

      </div>

      {/* INPUT */}
      <div className="p-4 border-t border-gray-800 flex gap-2">

        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askAI()}
          placeholder="Ask your PDF..."
          className="flex-1 p-3 rounded-lg bg-gray-900 text-white"
        />

        <button
          onClick={askAI}
          className="bg-blue-600 px-5 py-3 rounded-lg"
        >
          Send
        </button>

      </div>
    </div>
  );
}