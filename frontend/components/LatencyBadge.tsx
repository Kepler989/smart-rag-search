"use client";

import { Zap, Brain, Search, Clock } from "lucide-react";
import type { LatencyMetrics } from "@/lib/types";

interface LatencyBadgeProps {
  latency: LatencyMetrics;
}

interface MetricPillProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}

function MetricPill({ icon, label, value, color }: MetricPillProps) {
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs ${color}`}>
      {icon}
      <span className="font-medium">{value.toFixed(0)}ms</span>
      <span className="opacity-70">{label}</span>
    </div>
  );
}

export default function LatencyBadge({ latency }: LatencyBadgeProps) {
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {latency.cached && (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
          <Zap className="w-3 h-3" />
          <span className="font-medium">Cached</span>
        </div>
      )}
      <MetricPill
        icon={<Brain className="w-3 h-3" />}
        label="embed"
        value={latency.embedding_ms}
        color="bg-violet-500/15 text-violet-400 border border-violet-500/20"
      />
      <MetricPill
        icon={<Search className="w-3 h-3" />}
        label="vector"
        value={latency.vector_search_ms}
        color="bg-blue-500/15 text-blue-400 border border-blue-500/20"
      />
      <MetricPill
        icon={<Zap className="w-3 h-3" />}
        label="LLM"
        value={latency.llm_generation_ms}
        color="bg-amber-500/15 text-amber-400 border border-amber-500/20"
      />
      <MetricPill
        icon={<Clock className="w-3 h-3" />}
        label="total"
        value={latency.total_ms}
        color="bg-white/5 text-slate-400 border border-white/10"
      />
    </div>
  );
}
