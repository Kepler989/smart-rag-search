import Link from "next/link";
import { ArrowLeft, Brain } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0d0f17] text-white flex flex-col items-center justify-center p-6 text-center">
      <div className="p-3 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-700 mb-6 shadow-lg shadow-violet-500/20">
        <Brain className="w-10 h-10 text-white" />
      </div>

      <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-indigo-400 mb-2">
        404
      </h1>
      <h2 className="text-2xl font-bold text-slate-200 mb-3">
        Page Not Found
      </h2>
      <p className="text-slate-400 max-w-md mb-8 text-sm">
        The page you are looking for does not exist or has been moved.
      </p>

      <Link
        href="/"
        className="flex items-center gap-2 px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm transition-all duration-200 shadow-lg shadow-violet-600/30"
      >
        <ArrowLeft className="w-4 h-4" />
        Return to Smart RAG Search
      </Link>
    </div>
  );
}
