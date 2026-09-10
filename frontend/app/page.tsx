"use client";

import { useState } from "react";
import {
  Brain,
  Database,
  Zap,
  ChevronRight,
  Upload,
  MessageSquare,
  Activity,
  ExternalLink,
} from "lucide-react";
import ChatInterface from "@/components/ChatInterface";
import DocumentUploader from "@/components/DocumentUploader";
import DocumentList from "@/components/DocumentList";
import { useDocuments } from "@/hooks/useDocuments";

type Tab = "chat" | "upload";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const { documents, isLoading, removeDocument, refresh } = useDocuments();

  const toggleDocSelection = (id: string, selected: boolean) => {
    setSelectedDocIds((prev) => {
      const next = new Set(prev);
      if (selected) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const readyDocs = documents.filter((d) => d.status === "ready");
  const processingDocs = documents.filter(
    (d) => d.status === "pending" || d.status === "processing"
  );

  return (
    <div className="bg-animated-gradient h-screen flex flex-col overflow-hidden">
      {/* ── Top Nav ── */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/6 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 p-2 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-700">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold text-base leading-none">Smart RAG Search</h1>
            <p className="text-slate-500 text-[10px] mt-0.5">AI Document Assistant · Gemini 2.5 Flash</p>
          </div>
        </div>

        {/* Status pills */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/8 text-xs text-slate-400">
            <Database className="w-3 h-3 text-violet-400" />
            <span>{readyDocs.length} docs indexed</span>
          </div>
          {processingDocs.length > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
              <Activity className="w-3 h-3 animate-pulse" />
              <span>{processingDocs.length} processing</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400">
            <Zap className="w-3 h-3" />
            <span>Redis cached</span>
          </div>
        </div>

        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/8 transition-all duration-200"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </header>

      {/* ── Main Layout ── */}
      <main className="flex-1 flex overflow-hidden">
        {/* ── Left Sidebar ── */}
        <aside className="w-72 border-r border-white/6 flex flex-col shrink-0 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-white/6 shrink-0">
            {(["chat", "upload"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  flex-1 flex items-center justify-center gap-2 py-3 text-xs font-semibold uppercase tracking-wider transition-all duration-200
                  ${activeTab === tab
                    ? "text-violet-400 border-b-2 border-violet-500 bg-violet-500/5"
                    : "text-slate-500 hover:text-slate-300"
                  }
                `}
              >
                {tab === "chat" ? <MessageSquare className="w-3.5 h-3.5" /> : <Upload className="w-3.5 h-3.5" />}
                {tab}
              </button>
            ))}
          </div>

          {/* Sidebar Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === "upload" ? (
              <div className="flex flex-col gap-4">
                <DocumentUploader onUploadComplete={refresh} />
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Documents
                  </h2>
                  {selectedDocIds.size > 0 && (
                    <button
                      onClick={() => setSelectedDocIds(new Set())}
                      className="text-[10px] text-violet-400 hover:text-violet-300"
                    >
                      Clear filter
                    </button>
                  )}
                </div>
                <DocumentList
                  documents={documents}
                  isLoading={isLoading}
                  onDelete={removeDocument}
                  onSelect={toggleDocSelection}
                  selectedIds={selectedDocIds}
                />
                {selectedDocIds.size > 0 && (
                  <div className="px-3 py-2 rounded-xl bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 flex items-center gap-2">
                    <ChevronRight className="w-3 h-3 shrink-0" />
                    Searching {selectedDocIds.size} selected document{selectedDocIds.size > 1 ? "s" : ""}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar Footer */}
          <div className="shrink-0 p-4 border-t border-white/6">
            <div className="flex flex-col gap-1.5 text-[10px] text-slate-600">
              <div className="flex items-center justify-between">
                <span>Embedding Model</span>
                <span className="text-slate-500">text-embedding-004</span>
              </div>
              <div className="flex items-center justify-between">
                <span>LLM</span>
                <span className="text-slate-500">gemini-2.5-flash</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Vector Index</span>
                <span className="text-slate-500">pgvector HNSW</span>
              </div>
            </div>
          </div>
        </aside>

        {/* ── Chat Area ── */}
        <section className="flex-1 flex flex-col overflow-hidden">
          <ChatInterface
            documentIds={selectedDocIds.size > 0 ? Array.from(selectedDocIds) : undefined}
          />
        </section>
      </main>
    </div>
  );
}
