"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, File, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { uploadDocument } from "@/lib/api";
import type { DocumentStatus } from "@/lib/types";

interface FileState {
  file: File;
  status: "pending" | "uploading" | "processing" | "done" | "error";
  documentId?: string;
  error?: string;
  progress: number;
}

interface DocumentUploaderProps {
  onUploadComplete?: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FileIcon({ type }: { type: string }) {
  if (type === "pdf") return <FileText className="w-4 h-4 text-red-400" />;
  if (type === "md" || type === "markdown") return <File className="w-4 h-4 text-blue-400" />;
  return <File className="w-4 h-4 text-slate-400" />;
}

export default function DocumentUploader({ onUploadComplete }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FileState[]>([]);

  const processFiles = useCallback(
    async (newFiles: File[]) => {
      const allowed = [".pdf", ".md", ".markdown", ".txt"];
      const valid = newFiles.filter((f) =>
        allowed.some((ext) => f.name.toLowerCase().endsWith(ext))
      );

      if (valid.length === 0) return;

      const initialStates: FileState[] = valid.map((f) => ({
        file: f,
        status: "pending",
        progress: 0,
      }));

      setFiles((prev) => [...prev, ...initialStates]);

      // Upload each file
      for (let i = 0; i < valid.length; i++) {
        const file = valid[i];
        const idx = files.length + i;

        setFiles((prev) =>
          prev.map((fs, j) =>
            j === idx ? { ...fs, status: "uploading", progress: 30 } : fs
          )
        );

        try {
          const response = await uploadDocument(file);
          setFiles((prev) =>
            prev.map((fs, j) =>
              j === idx
                ? { ...fs, status: "processing", documentId: response.document_id, progress: 60 }
                : fs
            )
          );

          // Simulate completion after a short delay (backend will process async)
          setTimeout(() => {
            setFiles((prev) =>
              prev.map((fs, j) =>
                j === idx ? { ...fs, status: "done", progress: 100 } : fs
              )
            );
            onUploadComplete?.();
          }, 1500);
        } catch (err) {
          setFiles((prev) =>
            prev.map((fs, j) =>
              j === idx
                ? {
                    ...fs,
                    status: "error",
                    error: err instanceof Error ? err.message : "Upload failed",
                    progress: 0,
                  }
                : fs
            )
          );
        }
      }
    },
    [files.length, onUploadComplete]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFiles = Array.from(e.dataTransfer.files);
      processFiles(droppedFiles);
    },
    [processFiles]
  );

  const onFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = Array.from(e.target.files ?? []);
      processFiles(selected);
      e.target.value = "";
    },
    [processFiles]
  );

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, j) => j !== idx));
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
          transition-all duration-200 group
          ${isDragging
            ? "border-violet-500 bg-violet-500/10 scale-[1.01]"
            : "border-white/10 bg-white/5 hover:border-violet-500/50 hover:bg-white/8"
          }
        `}
      >
        <input
          id="file-upload"
          type="file"
          multiple
          accept=".pdf,.md,.markdown,.txt"
          onChange={onFileInput}
          className="absolute inset-0 opacity-0 cursor-pointer"
        />
        <div className="flex flex-col items-center gap-3 pointer-events-none">
          <div className={`
            p-4 rounded-full transition-all duration-200
            ${isDragging ? "bg-violet-500/20" : "bg-white/5 group-hover:bg-violet-500/10"}
          `}>
            <Upload className={`w-8 h-8 transition-colors ${isDragging ? "text-violet-400" : "text-slate-400 group-hover:text-violet-400"}`} />
          </div>
          <div>
            <p className="text-white font-medium">Drop files here or click to upload</p>
            <p className="text-slate-400 text-sm mt-1">Supports PDF, Markdown, and TXT — up to 50 MB</p>
          </div>
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          {files.map((fs, idx) => {
            const ext = fs.file.name.split(".").pop() ?? "";
            return (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/8"
              >
                <FileIcon type={ext} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-white truncate">{fs.file.name}</p>
                    <span className="text-xs text-slate-500 shrink-0">{formatSize(fs.file.size)}</span>
                  </div>
                  {/* Progress bar */}
                  {(fs.status === "uploading" || fs.status === "processing") && (
                    <div className="mt-1.5 h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-500"
                        style={{ width: `${fs.progress}%` }}
                      />
                    </div>
                  )}
                  {fs.status === "error" && (
                    <p className="text-xs text-red-400 mt-0.5">{fs.error}</p>
                  )}
                </div>
                {/* Status icon */}
                <div className="shrink-0">
                  {fs.status === "uploading" || fs.status === "processing" ? (
                    <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                  ) : fs.status === "done" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : fs.status === "error" ? (
                    <XCircle className="w-4 h-4 text-red-400" />
                  ) : null}
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  className="shrink-0 p-1 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors"
                >
                  <XCircle className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
