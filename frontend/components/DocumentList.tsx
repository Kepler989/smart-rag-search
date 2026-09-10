"use client";

import { useState } from "react";
import {
  FileText, File, Loader2, CheckCircle2, XCircle, Clock,
  Trash2, ChevronRight, Database, Hash
} from "lucide-react";
import type { Document, DocumentStatus } from "@/lib/types";

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSelect?: (id: string, selected: boolean) => void;
  selectedIds?: Set<string>;
}

function StatusChip({ status }: { status: DocumentStatus }) {
  const config = {
    pending: { icon: <Clock className="w-3 h-3" />, label: "Pending", cls: "bg-amber-500/15 text-amber-400 border-amber-500/20" },
    processing: { icon: <Loader2 className="w-3 h-3 animate-spin" />, label: "Processing", cls: "bg-blue-500/15 text-blue-400 border-blue-500/20" },
    ready: { icon: <CheckCircle2 className="w-3 h-3" />, label: "Ready", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
    failed: { icon: <XCircle className="w-3 h-3" />, label: "Failed", cls: "bg-red-500/15 text-red-400 border-red-500/20" },
  };
  const { icon, label, cls } = config[status];
  return (
    <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {icon} {label}
    </span>
  );
}

function FileIcon({ type }: { type: string }) {
  if (type === "pdf") return <FileText className="w-4 h-4 text-red-400" />;
  if (type === "md" || type === "markdown") return <File className="w-4 h-4 text-blue-400" />;
  return <File className="w-4 h-4 text-slate-400" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentList({
  documents,
  isLoading,
  onDelete,
  onSelect,
  selectedIds = new Set(),
}: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Database className="w-10 h-10 text-slate-600 mb-3" />
        <p className="text-slate-400 text-sm">No documents yet</p>
        <p className="text-slate-600 text-xs mt-1">Upload a document to get started</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {onSelect && documents.filter(d => d.status === "ready").length > 0 && (
        <p className="text-xs text-slate-500 px-1">
          Select documents to filter search (none = search all)
        </p>
      )}
      {documents.map((doc) => {
        const isSelected = selectedIds.has(doc.id);
        const isReady = doc.status === "ready";

        return (
          <div
            key={doc.id}
            className={`
              flex items-start gap-3 p-3 rounded-xl border transition-all duration-200 group
              ${isSelected
                ? "bg-violet-500/10 border-violet-500/30"
                : "bg-white/4 border-white/8 hover:bg-white/6"
              }
              ${isReady && onSelect ? "cursor-pointer" : ""}
            `}
            onClick={() => isReady && onSelect?.(doc.id, !isSelected)}
          >
            {/* Checkbox indicator */}
            {onSelect && isReady && (
              <div className={`
                mt-0.5 w-4 h-4 rounded-md border-2 flex items-center justify-center shrink-0 transition-all
                ${isSelected ? "bg-violet-500 border-violet-500" : "border-white/20"}
              `}>
                {isSelected && <ChevronRight className="w-3 h-3 text-white" />}
              </div>
            )}

            <FileIcon type={doc.file_type} />

            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate font-medium">{doc.original_filename}</p>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <StatusChip status={doc.status} />
                {doc.total_chunks > 0 && (
                  <span className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Hash className="w-2.5 h-2.5" /> {doc.total_chunks} chunks
                  </span>
                )}
                <span className="text-[10px] text-slate-600">{formatSize(doc.file_size_bytes)}</span>
              </div>
              {doc.error_message && (
                <p className="text-[10px] text-red-400 mt-1 truncate">{doc.error_message}</p>
              )}
            </div>

            <button
              onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
              disabled={deletingId === doc.id}
              className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-all duration-200 shrink-0"
            >
              {deletingId === doc.id ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Trash2 className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        );
      })}
    </div>
  );
}
