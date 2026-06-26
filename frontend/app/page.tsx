"use client";

import {
  ChangeEvent,
  DragEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type UploadResponse = {
  message: string;
  filename: string;
  chunks: number;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string;
      error?: string;
    };

    return (
      payload.detail ??
      payload.error ??
      `Request failed with status ${response.status}.`
    );
  } catch {
    return `Request failed with status ${response.status}.`;
  }
}

export default function Home() {
  const [question, setQuestion] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);

  const [uploadedFileName, setUploadedFileName] =
    useState<string>("");

  const [uploadSummary, setUploadSummary] =
    useState<string>("");

  const [uploadError, setUploadError] =
    useState<string>("");

  const [chatError, setChatError] =
    useState<string>("");

  const [isUploading, setIsUploading] =
    useState<boolean>(false);

  const [isSending, setIsSending] =
    useState<boolean>(false);

  const [isDragging, setIsDragging] =
    useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isPdfReady = Boolean(uploadedFileName);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isSending]);

  const uploadPDF = async (file: File): Promise<void> => {
    setUploadError("");
    setChatError("");

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setUploadError("Please select a PDF file.");
      return;
    }

    const maxSize = 25 * 1024 * 1024;

    if (file.size > maxSize) {
      setUploadError("The PDF must be smaller than 25 MB.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setUploadedFileName("");
    setUploadSummary("");

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data = (await response.json()) as UploadResponse;

      setUploadedFileName(data.filename);
      setUploadSummary(
        `${data.chunks} searchable chunks created`,
      );

      setMessages([
        {
          id: createId(),
          role: "assistant",
          content:
            `"${data.filename}" is ready. ` +
            "Ask a question about the document.",
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "PDF upload failed.";

      setUploadError(message);
    } finally {
      setIsUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleFileInput = (
    event: ChangeEvent<HTMLInputElement>,
  ): void => {
    const file = event.target.files?.[0];

    if (file) {
      void uploadPDF(file);
    }
  };

  const handleDrop = (
    event: DragEvent<HTMLDivElement>,
  ): void => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      void uploadPDF(file);
    }
  };

  const askAI = async (): Promise<void> => {
    const cleanQuestion = question.trim();

    if (
      !cleanQuestion ||
      !isPdfReady ||
      isSending ||
      isUploading
    ) {
      return;
    }

    setChatError("");

    const userMessage: Message = {
      id: createId(),
      role: "user",
      content: cleanQuestion,
    };

    const assistantMessageId = createId();

    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
      assistantMessage,
    ]);

    setQuestion("");
    setIsSending(true);

    try {
      const response = await fetch(
        `${API_URL}/ask-stream?q=${encodeURIComponent(
          cleanQuestion,
        )}`,
      );

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      if (!response.body) {
        throw new Error(
          "The backend returned no response stream.",
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let completeAnswer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          completeAnswer += decoder.decode();
          break;
        }

        completeAnswer += decoder.decode(value, {
          stream: true,
        });

        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  content: completeAnswer,
                }
              : message,
          ),
        );
      }

      if (!completeAnswer.trim()) {
        throw new Error(
          "The model returned an empty response.",
        );
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to contact the backend.";

      setChatError(message);

      setMessages((previous) =>
        previous.map((item) =>
          item.id === assistantMessageId
            ? {
                ...item,
                content: `Error: ${message}`,
              }
            : item,
        ),
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleQuestionKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ): void => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void askAI();
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[330px_1fr]">
        <aside className="border-b border-slate-800 bg-slate-950/80 p-5 lg:border-b-0 lg:border-r">
          <div className="mb-8">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-xl shadow-lg shadow-blue-950">
                AI
              </div>

              <div>
                <h1 className="font-semibold tracking-tight">
                  PDF Intelligence
                </h1>

                <p className="text-xs text-slate-400">
                  Local RAG with LLaMA 3
                </p>
              </div>
            </div>
          </div>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium">
                Knowledge source
              </h2>

              {isPdfReady && (
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                  Ready
                </span>
              )}
            </div>

            <div
              onDragEnter={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => {
                setIsDragging(false);
              }}
              onDrop={handleDrop}
              className={`rounded-2xl border border-dashed p-5 transition ${
                isDragging
                  ? "border-blue-400 bg-blue-500/10"
                  : "border-slate-700 bg-slate-900/60"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf,.pdf"
                onChange={handleFileInput}
                className="hidden"
              />

              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800 text-2xl">
                📄
              </div>

              <p className="mt-4 text-sm font-medium">
                Drop a PDF here
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-400">
                Select one text-based PDF up to 25 MB.
              </p>

              <button
                type="button"
                disabled={isUploading}
                onClick={() =>
                  fileInputRef.current?.click()
                }
                className="mt-4 w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isUploading
                  ? "Processing PDF..."
                  : "Choose PDF"}
              </button>
            </div>

            {uploadedFileName && (
              <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <p className="wrap-break-words text-sm font-medium text-emerald-300">
                  {uploadedFileName}
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  {uploadSummary}
                </p>
              </div>
            )}

            {uploadError && (
              <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">
                {uploadError}
              </div>
            )}
          </section>

          <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-sm font-medium">
              Local technology stack
            </h3>

            <div className="mt-3 space-y-2 text-xs text-slate-400">
              <p>Next.js + TypeScript</p>
              <p>FastAPI + ChromaDB</p>
              <p>SentenceTransformers</p>
              <p>Ollama + LLaMA 3</p>
            </div>
          </section>
        </aside>

        <section className="flex min-h-[70vh] flex-col">
          <header className="flex h-20 items-center justify-between border-b border-slate-800 px-5 sm:px-8">
            <div>
              <h2 className="font-semibold">
                Document chat
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Answers are grounded in the uploaded PDF.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  isPdfReady
                    ? "bg-emerald-400"
                    : "bg-amber-400"
                }`}
              />

              {isPdfReady
                ? "PDF ready"
                : "Upload required"}
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-8">
            <div className="mx-auto max-w-4xl space-y-6">
              {messages.length === 0 && (
                <div className="flex min-h-[50vh] items-center justify-center">
                  <div className="max-w-xl text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-blue-600/10 text-3xl">
                      💬
                    </div>

                    <h3 className="mt-5 text-2xl font-semibold tracking-tight">
                      Chat with your PDF
                    </h3>

                    <p className="mt-3 text-sm leading-6 text-slate-400">
                      Upload a PDF from the left panel.
                      After processing completes, ask questions
                      about its content.
                    </p>
                  </div>
                </div>
              )}

              {messages.map((message) => {
                const isUser = message.role === "user";

                return (
                  <div
                    key={message.id}
                    className={`flex ${
                      isUser
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[88%] rounded-3xl px-5 py-4 text-sm leading-7 shadow-sm sm:max-w-[75%] ${
                        isUser
                          ? "rounded-br-md bg-blue-600 text-white"
                          : "rounded-bl-md border border-slate-800 bg-slate-900 text-slate-200"
                      }`}
                    >
                      {message.content ? (
                        <p className="whitespace-pre-wrap">
                          {message.content}
                        </p>
                      ) : (
                        <div className="flex items-center gap-1.5 py-1">
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <footer className="border-t border-slate-800 bg-slate-950/90 p-4 sm:p-6">
            <div className="mx-auto max-w-4xl">
              {chatError && (
                <div className="mb-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
                  {chatError}
                </div>
              )}

              <div className="flex items-end gap-3 rounded-2xl border border-slate-700 bg-slate-900 p-2 shadow-2xl shadow-black/20 focus-within:border-blue-500">
                <textarea
                  rows={1}
                  value={question}
                  disabled={
                    !isPdfReady ||
                    isSending ||
                    isUploading
                  }
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                  onKeyDown={handleQuestionKeyDown}
                  placeholder={
                    isPdfReady
                      ? "Ask a question about the PDF..."
                      : "Upload a PDF before asking questions"
                  }
                  className="max-h-40 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-slate-500 disabled:cursor-not-allowed"
                />

                <button
                  type="button"
                  onClick={() => void askAI()}
                  disabled={
                    !isPdfReady ||
                    !question.trim() ||
                    isSending ||
                    isUploading
                  }
                  className="flex h-11 min-w-20 items-center justify-center rounded-xl bg-blue-600 px-5 text-sm font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                  {isSending ? "Stop" : "Send"}
                </button>
              </div>

              <p className="mt-3 text-center text-xs text-slate-500">
                Press Enter to send. Use Shift + Enter
                for a new line.
              </p>
            </div>
          </footer>
        </section>
      </div>
    </main>
  );
}