"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { Send, Square, Trash2, MessageSquare } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";

interface ChatInterfaceProps {
  documentIds?: string[];
}

export default function ChatInterface({ documentIds }: ChatInterfaceProps) {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      const query = input.trim();
      if (!query || isLoading) return;
      setInput("");
      await sendMessage(query, documentIds);
    },
    [input, isLoading, sendMessage, documentIds]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/8">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-semibold text-white">Chat</span>
          <span className="text-xs text-slate-500">{messages.length} messages</span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-all duration-200"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4 scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
            <div className="p-5 rounded-2xl bg-white/5 border border-white/8 mb-4">
              <MessageSquare className="w-10 h-10 text-violet-400 mx-auto" />
            </div>
            <h3 className="text-white font-semibold text-lg">Ask anything about your documents</h3>
            <p className="text-slate-400 text-sm mt-2 max-w-sm">
              Upload PDFs, Markdown, or text files, then ask questions and get cited answers powered by Gemini AI.
            </p>
            <div className="grid grid-cols-1 gap-2 mt-6 w-full max-w-sm">
              {[
                "What is the main topic of the document?",
                "Summarize the key findings",
                "What are the conclusions?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => { setInput(suggestion); textareaRef.current?.focus(); }}
                  className="text-left px-4 py-2.5 rounded-xl bg-white/5 border border-white/8 text-sm text-slate-300 hover:bg-white/10 hover:border-violet-500/30 transition-all duration-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="px-4 py-3 border-t border-white/8">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents…"
              rows={1}
              className="
                w-full resize-none rounded-xl px-4 py-3 pr-4
                bg-white/6 border border-white/10
                text-white placeholder-slate-500 text-sm
                focus:outline-none focus:border-violet-500/60 focus:bg-white/8
                transition-all duration-200
                min-h-[48px] max-h-[160px]
              "
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            id="send-button"
            className="
              flex items-center justify-center
              w-12 h-12 rounded-xl shrink-0
              bg-gradient-to-br from-violet-600 to-indigo-700
              hover:from-violet-500 hover:to-indigo-600
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-all duration-200
              shadow-lg shadow-violet-500/25
            "
          >
            {isLoading ? (
              <Square className="w-4 h-4 text-white" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        </form>
        <p className="text-[10px] text-slate-600 text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
