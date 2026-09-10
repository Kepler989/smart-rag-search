"use client";

import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { streamQuery } from "@/lib/api";
import type { ChatMessage, LatencyMetrics, QueryRequest, SourceCitation } from "@/lib/types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  const sendMessage = useCallback(async (query: string, documentIds?: string[]) => {
    if (!query.trim() || isLoading) return;

    setError(null);
    abortRef.current = false;

    // Add user message
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    // Add streaming placeholder for assistant
    const assistantId = uuidv4();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    const request: QueryRequest = {
      query,
      top_k: 5,
      document_ids: documentIds ?? null,
    };

    let accumulatedContent = "";
    let finalSources: SourceCitation[] = [];
    let finalLatency: LatencyMetrics | undefined;

    try {
      await streamQuery(
        request,
        // onToken
        (token) => {
          if (abortRef.current) return;
          accumulatedContent += token;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: accumulatedContent } : m
            )
          );
        },
        // onSources
        (sources) => {
          finalSources = sources;
        },
        // onLatency
        (latency) => {
          finalLatency = latency;
        },
        // onDone
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: accumulatedContent || "No response generated.",
                    sources: finalSources,
                    latency: finalLatency,
                    isStreaming: false,
                  }
                : m
            )
          );
          setIsLoading(false);
        },
        // onError
        (err) => {
          setError(err);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `Error: ${err}`, isStreaming: false }
                : m
            )
          );
          setIsLoading(false);
        }
      );
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Unknown error";
      setError(errMsg);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error: ${errMsg}`, isStreaming: false }
            : m
        )
      );
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearMessages = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearMessages };
}
