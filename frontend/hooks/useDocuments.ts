"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import type { Document } from "@/lib/types";

const POLL_INTERVAL_MS = 3000;

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    load();
  }, [load]);

  // Poll while any document is still processing
  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );
    if (!hasPending) return;

    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [documents, load]);

  const removeDocument = useCallback(
    async (id: string) => {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
    },
    []
  );

  return { documents, total, isLoading, error, refresh: load, removeDocument };
}
