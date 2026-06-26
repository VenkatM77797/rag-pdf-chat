"use client";

import { useState } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

export default function Home() {
  const [question, setQuestion] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // 🧠 ASK AI FUNCTION
  const askAI = async () => {
    if (!question.trim()) return;

    const userMessage: Message = {
      role: "user",
      text: question,
    };

    const currentQuestion = question;

    // Add user + empty bot message
    setMessages((prev) => [
      ...prev,
      userMessage,
      { role: "bot", text: "" },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/ask?q=${encodeURIComponent(currentQuestion)}`
      );

      if (!res.ok) {
        throw new Error("Backend error");
      }

      const data = await res.json();

      const answer = data.answer || "No response";

      // Fill bot response
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: "bot",
          text: answer,
        };
        return copy;
      });
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: "bot",
          text: "❌ Error connecting to backend",
        };
        return copy;
      });
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-black text-white">

      {/* HEADER */}
      <div className="p-4 border-b border-gray-800 text-center font-bold text-lg">
        🧠 RAG Chat (LLaMA 3 + FastAPI)
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
              className={`px-4 py-2 rounded-2xl max-w-[70%] text-sm whitespace-pre-wrap ${
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
            AI is thinking...
          </div>
        )}

      </div>

      {/* INPUT AREA */}
      <div className="p-4 border-t border-gray-800 flex gap-2">

        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askAI()}
          placeholder="Ask your PDF..."
          className="flex-1 p-3 rounded-lg bg-gray-900 text-white outline-none border border-gray-700"
        />

        <button
          onClick={askAI}
          className="bg-blue-600 px-5 py-3 rounded-lg hover:bg-blue-700"
        >
          Send
        </button>

      </div>
    </div>
  );
}