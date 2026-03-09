"use client";

import { Upload, CheckCircle, AlertCircle, Loader2, X } from "lucide-react";
import { useCallback, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface FileUploadState {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  progress: number;
  runAccession?: string;
  error?: string;
}

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
  experimentAccession?: string;
}

async function computeMd5Hex(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}

export function UploadStep({ files, onChange, experimentAccession }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [uploads, setUploads] = useState<FileUploadState[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = Array.from(e.dataTransfer.files);
      onChange([...files, ...dropped]);
    },
    [files, onChange]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        onChange([...files, ...Array.from(e.target.files)]);
      }
    },
    [files, onChange]
  );

  const removeFile = useCallback(
    (index: number) => {
      onChange(files.filter((_, i) => i !== index));
    },
    [files, onChange]
  );

  const uploadAll = useCallback(async () => {
    if (!experimentAccession || files.length === 0) return;
    setIsUploading(true);

    const states: FileUploadState[] = files.map((f) => ({
      file: f,
      status: "pending",
      progress: 0,
    }));
    setUploads([...states]);

    for (let i = 0; i < states.length; i++) {
      const file = states[i].file;
      states[i].status = "uploading";
      states[i].progress = 10;
      setUploads([...states]);

      try {
        // Compute checksum
        const checksum = await computeMd5Hex(file);
        states[i].progress = 20;
        setUploads([...states]);

        // Determine file type from extension
        const ext = file.name.split(".").pop()?.toLowerCase() || "";
        const fileTypeMap: Record<string, string> = {
          fastq: "FASTQ", "fastq.gz": "FASTQ", fq: "FASTQ", "fq.gz": "FASTQ",
          bam: "BAM", cram: "CRAM", vcf: "VCF", "vcf.gz": "VCF",
          bed: "BED", idat: "IDAT", gtc: "GTC", ped: "PED",
        };
        const fileType = fileTypeMap[ext] || "OTHER";

        // 1. Initiate upload — get presigned URL
        const initRes = await api.post("/upload/initiate", {
          experiment_accession: experimentAccession,
          filename: file.name,
          file_size: file.size,
          checksum_md5: checksum,
          file_type: fileType,
        });
        const { upload_id, presigned_url } = initRes.data;
        states[i].progress = 40;
        setUploads([...states]);

        // 2. PUT file to presigned URL (direct to MinIO)
        await fetch(presigned_url, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": "application/octet-stream" },
        });
        states[i].progress = 80;
        setUploads([...states]);

        // 3. Complete upload
        const completeRes = await api.post("/upload/complete", {
          upload_id,
          checksum_md5: checksum,
        });
        states[i].status = "done";
        states[i].progress = 100;
        states[i].runAccession = completeRes.data.run_accession;
      } catch (err) {
        states[i].status = "error";
        states[i].error = err instanceof Error ? err.message : "Upload failed";
      }
      setUploads([...states]);
    }
    setIsUploading(false);
  }, [files, experimentAccession]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Upload Files</h3>
      <div
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors ${
          dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
        <p className="mb-2 text-sm text-muted-foreground">
          Drag and drop FASTQ, BAM, VCF, or other files here
        </p>
        <label className="cursor-pointer text-sm font-medium text-primary hover:underline">
          or click to browse
          <input
            type="file"
            multiple
            className="hidden"
            onChange={handleFileInput}
          />
        </label>
      </div>

      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              {files.length} file(s) selected
            </p>
            {experimentAccession && !isUploading && (
              <Button size="sm" onClick={uploadAll}>
                <Upload className="mr-1 h-4 w-4" />
                Upload to Storage
              </Button>
            )}
            {!experimentAccession && (
              <p className="text-xs text-yellow-600">
                Complete previous steps first
              </p>
            )}
          </div>

          <ul className="space-y-2">
            {files.map((f, i) => {
              const state = uploads[i];
              return (
                <li
                  key={i}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    {state?.status === "done" && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {state?.status === "error" && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    {state?.status === "uploading" && (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                    <span className="font-mono text-sm">{f.name}</span>
                    {state?.runAccession && (
                      <Badge variant="outline" className="ml-2">
                        {state.runAccession}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {(f.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                    {state && state.status !== "pending" && (
                      <span className="text-xs text-muted-foreground">
                        {state.progress}%
                      </span>
                    )}
                    {(!state || state.status === "pending") && (
                      <button
                        onClick={() => removeFile(i)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
