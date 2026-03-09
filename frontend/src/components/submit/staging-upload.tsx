"use client";

import { useCallback, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, Trash2, CheckCircle, AlertCircle, Loader2, Info, ChevronDown, ChevronUp, Terminal, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";

interface StagedFile {
  id: string;
  filename: string;
  file_size: number;
  checksum_md5: string;
  status: string;
}

interface FileUploadState {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  progress: number;
  error?: string;
}

interface Props {
  hasStagedFiles: boolean;
  onStagedFilesChange: (has: boolean) => void;
}

export function StagingUpload({ onStagedFilesChange }: Props) {
  const queryClient = useQueryClient();
  const [dragOver, setDragOver] = useState(false);
  const [uploads, setUploads] = useState<FileUploadState[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const { data: stagedFiles = [], refetch: refetchStaged } = useQuery<StagedFile[]>({
    queryKey: ["staging-files"],
    queryFn: () => api.get("/staging/files").then((r) => r.data),
    refetchInterval: isUploading ? 3000 : false,
  });

  // Update parent when staged files change
  const refreshStaged = useCallback(async () => {
    const result = await refetchStaged();
    const files = result.data ?? [];
    onStagedFilesChange(files.length > 0);
  }, [refetchStaged, onStagedFilesChange]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = Array.from(e.dataTransfer.files);
      uploadFiles(dropped);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        uploadFiles(Array.from(e.target.files));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const uploadFiles = async (filesToUpload: File[]) => {
    if (filesToUpload.length === 0) return;
    setIsUploading(true);

    const states: FileUploadState[] = filesToUpload.map((f) => ({
      file: f,
      status: "pending",
      progress: 0,
    }));
    setUploads((prev) => [...prev, ...states]);

    for (let i = 0; i < states.length; i++) {
      const updateState = () =>
        setUploads((prev) => {
          const updated = [...prev];
          const offset = updated.length - states.length;
          updated[offset + i] = { ...states[i] };
          return updated;
        });

      states[i].status = "uploading";
      states[i].progress = 20;
      updateState();

      try {
        // Direct upload through backend — MD5 computed server-side
        const formData = new FormData();
        formData.append("file", states[i].file);

        await api.post("/staging/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (e) => {
            if (e.total) {
              states[i].progress = Math.round(20 + (e.loaded / e.total) * 80);
              updateState();
            }
          },
        });

        states[i].status = "done";
        states[i].progress = 100;
      } catch (err) {
        states[i].status = "error";
        states[i].error = err instanceof Error ? err.message : "Upload failed";
      }

      updateState();
    }

    setIsUploading(false);
    await refreshStaged();
  };

  const deleteFile = useCallback(
    async (id: string) => {
      try {
        await api.delete(`/staging/files/${id}`);
        await refreshStaged();
        queryClient.invalidateQueries({ queryKey: ["staging-files"] });
      } catch {
        // silently fail
      }
    },
    [refreshStaged, queryClient]
  );

  const activeUploads = uploads.filter((u) => u.status !== "done");

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Upload Files to Staging</h3>

      {/* Drag and drop zone */}
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

      {/* Active uploads progress */}
      {activeUploads.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Uploading...</p>
          {activeUploads.map((u, i) => (
            <div key={i} className="flex items-center gap-2 rounded-md border px-3 py-2">
              {u.status === "uploading" && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
              {u.status === "error" && <AlertCircle className="h-4 w-4 text-red-500" />}
              {u.status === "pending" && <div className="h-4 w-4" />}
              <span className="flex-1 font-mono text-sm">{u.file.name}</span>
              <span className="text-xs text-muted-foreground">{u.progress}%</span>
              {u.error && <span className="text-xs text-red-500">{u.error}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Staged files table */}
      {stagedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <p className="text-sm font-medium">{stagedFiles.length} file(s) staged</p>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>MD5</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {stagedFiles.map((f) => (
                <TableRow key={f.id}>
                  <TableCell className="font-mono text-sm">{f.filename}</TableCell>
                  <TableCell className="text-sm">
                    {(f.file_size / 1024 / 1024).toFixed(1)} MB
                  </TableCell>
                  <TableCell>
                    <code className="text-xs">{f.checksum_md5.slice(0, 12)}...</code>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">{f.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <button
                      onClick={() => deleteFile(f.id)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* FTP how-to */}
      <FtpHowTo />
    </div>
  );
}

/* ---------- FTP How-To Panel ---------- */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button onClick={copy} className="ml-2 inline-flex items-center text-muted-foreground hover:text-foreground">
      {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

function CodeBlock({ children }: { children: string }) {
  return (
    <div className="group relative mt-1 rounded-md bg-muted px-3 py-2 font-mono text-xs">
      <pre className="overflow-x-auto whitespace-pre-wrap break-all">{children}</pre>
      <div className="absolute right-2 top-2">
        <CopyButton text={children} />
      </div>
    </div>
  );
}

function FtpHowTo() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/30">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 p-3 text-left text-sm text-blue-800 dark:text-blue-200"
      >
        <Terminal className="h-4 w-4 shrink-0" />
        <span className="flex-1 font-medium">Upload via FTP/SFTP</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded && (
        <div className="space-y-4 border-t border-blue-200 px-4 py-3 text-sm dark:border-blue-900">
          <p className="text-muted-foreground">
            For large files (multi-GB FASTQ), FTP/SFTP is recommended over browser upload. Files
            uploaded via FTP are automatically checksummed and will appear in your staging area.
          </p>

          {/* Step 1 */}
          <div>
            <h4 className="font-semibold">1. Connect to the NFDP FTP server</h4>
            <p className="mt-1 text-xs text-muted-foreground">
              Use your NFDP portal credentials. Your FTP username follows the format{" "}
              <code className="rounded bg-muted px-1">nfdp_user_&#123;id&#125;</code> (provided during registration).
            </p>
            <CodeBlock>{`sftp nfdp_user_<your_id>@ftp.nfdp.sa`}</CodeBlock>
            <p className="mt-1 text-xs text-muted-foreground">
              Or using a GUI client (FileZilla, WinSCP, Cyberduck):
            </p>
            <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <span className="text-muted-foreground">Host:</span>
              <span className="font-mono">ftp.nfdp.sa</span>
              <span className="text-muted-foreground">Port:</span>
              <span className="font-mono">22 (SFTP) / 21 (FTP)</span>
              <span className="text-muted-foreground">Username:</span>
              <span className="font-mono">nfdp_user_&#123;your_id&#125;</span>
              <span className="text-muted-foreground">Password:</span>
              <span className="font-mono">(your portal password)</span>
            </div>
          </div>

          {/* Step 2 */}
          <div>
            <h4 className="font-semibold">2. Upload your files</h4>
            <p className="mt-1 text-xs text-muted-foreground">
              Upload FASTQ, BAM, VCF or other sequence files to your incoming directory.
              Use the <code className="rounded bg-muted px-1">put</code> command for individual files
              or <code className="rounded bg-muted px-1">mput</code> for multiple files.
            </p>
            <CodeBlock>{`# Upload paired-end FASTQ files\nsftp> put sample01_R1.fastq.gz\nsftp> put sample01_R2.fastq.gz\n\n# Or upload all .fastq.gz files at once\nsftp> mput *.fastq.gz`}</CodeBlock>
          </div>

          {/* Step 3 */}
          <div>
            <h4 className="font-semibold">3. Wait for processing</h4>
            <p className="mt-1 text-xs text-muted-foreground">
              The system automatically scans your FTP directory every 30 seconds. For each file it:
            </p>
            <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground space-y-0.5">
              <li>Computes the MD5 checksum</li>
              <li>Registers the file in your staging area</li>
              <li>Moves the file to the staging bucket</li>
            </ul>
            <p className="mt-1 text-xs text-muted-foreground">
              Files will appear in the staged files table above within ~1 minute.
            </p>
          </div>

          {/* Step 4 */}
          <div>
            <h4 className="font-semibold">4. File naming convention</h4>
            <p className="mt-1 text-xs text-muted-foreground">
              For automatic file-to-sample matching in the sample sheet step, name your files using
              the convention:
            </p>
            <CodeBlock>{`{sample_alias}_R1.fastq.gz    # forward reads\n{sample_alias}_R2.fastq.gz    # reverse reads`}</CodeBlock>
            <p className="mt-1 text-xs text-muted-foreground">
              Example: if your sample alias is <code className="rounded bg-muted px-1">CAMEL_001</code>,
              name files <code className="rounded bg-muted px-1">CAMEL_001_R1.fastq.gz</code> and{" "}
              <code className="rounded bg-muted px-1">CAMEL_001_R2.fastq.gz</code>.
              Alternatively, you can specify filenames explicitly in the sample sheet.
            </p>
          </div>

          {/* Tips */}
          <div className="flex items-start gap-2 rounded-md bg-blue-100/50 p-2 dark:bg-blue-900/20">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
            <div className="text-xs text-muted-foreground space-y-1">
              <p>
                <strong>Tip:</strong> Compute MD5 checksums locally before uploading so you can
                include them in your sample sheet for validation:
              </p>
              <CodeBlock>{`md5sum sample01_R1.fastq.gz sample01_R2.fastq.gz`}</CodeBlock>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
