"use client";

import { useState } from "react";
import { ChevronDown, FileText, BookOpen, Hash, ExternalLink } from "lucide-react";
import type { SourceCitation } from "@/lib/types";

interface SourceCitationPanelProps {
  sources: SourceCitation[];
}

function SimilarityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "from-emerald-500 to-green-400" :
    pct >= 60 ? "from-blue-500 to-violet-500" :
    "from-amber-500 to-orange-400";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  );
}

export default function SourceCitationPanel({ sources }: SourceCitationPanelProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  if (sources.length === 0) return null;

  return (
    <div className="mt-3 flex flex-col gap-1.5">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
        <BookOpen className="w-3 h-3" />
        Sources ({sources.length})
      </p>
      {sources.map((src, i) => (
        <div
          key={src.chunk_id}
          className="rounded-xl border border-white/8 bg-white/3 overflow-hidden"
        >
          {/* Header */}
          <button
            onClick={() => toggle(i)}
            className="w-full flex items-center gap-3 p-3 text-left hover:bg-white/5 transition-colors"
          >
            <FileText className="w-4 h-4 text-violet-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate font-medium">{src.document_name}</p>
              <div className="flex items-center gap-3 mt-0.5">
                {src.page_number && (
                  <span className="flex items-center gap-1 text-xs text-slate-400">
                    <Hash className="w-2.5 h-2.5" /> Page {src.page_number}
                  </span>
                )}
                {src.section && (
                  <span className="text-xs text-slate-400 truncate">§ {src.section}</span>
                )}
              </div>
              <div className="mt-1.5">
                <SimilarityBar score={src.similarity_score} />
              </div>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-500 shrink-0 transition-transform duration-200 ${
                expanded.has(i) ? "rotate-180" : ""
              }`}
            />
          </button>
          {/* Expanded content */}
          {expanded.has(i) && (
            <div className="px-3 pb-3 border-t border-white/5">
              <p className="text-xs text-slate-400 mt-2 leading-relaxed line-clamp-6 font-mono">
                {src.content_snippet}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
