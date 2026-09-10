"use client";

import { useRef, useEffect } from "react";
import { User, Bot, Loader2 } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import SourceCitationPanel from "./SourceCitationPanel";
import LatencyBadge from "./LatencyBadge";

interface MessageBubbleProps {
  message: ChatMessage;
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 h-5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5
          ${isUser
            ? "bg-gradient-to-br from-violet-500 to-indigo-600"
            : "bg-gradient-to-br from-slate-700 to-slate-800 border border-white/10"
          }
        `}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-violet-300" />
        )}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <div
          className={`
            px-4 py-3 rounded-2xl text-sm leading-relaxed
            ${isUser
              ? "bg-gradient-to-br from-violet-600 to-indigo-700 text-white rounded-tr-sm"
              : "bg-white/6 border border-white/8 text-slate-100 rounded-tl-sm"
            }
          `}
        >
          {message.isStreaming && !message.content ? (
            <TypingIndicator />
          ) : (
            <span className="whitespace-pre-wrap">{message.content}</span>
          )}
          {message.isStreaming && message.content && (
            <span className="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 animate-pulse align-middle" />
          )}
        </div>

        {/* Sources — only for assistant */}
        {!isUser && message.sources && message.sources.length > 0 && !message.isStreaming && (
          <SourceCitationPanel sources={message.sources} />
        )}

        {/* Latency metrics */}
        {!isUser && message.latency && !message.isStreaming && (
          <LatencyBadge latency={message.latency} />
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-slate-600 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
