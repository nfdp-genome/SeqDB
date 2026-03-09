"use client";

import { useState } from "react";
import { CheckCircle, AlertCircle, Loader2 } from "lucide-react";
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

interface ValidationRow {
  row_num: number;
  sample_alias: string;
  cells?: Record<string, { value: string; status: string }>;
  errors?: { row?: number; field: string; message: string }[];
  warnings?: { row?: number; field: string; message: string }[];
  forward_file?: { filename: string; md5: string } | null;
  reverse_file?: { filename: string; md5: string } | null;
}

interface Props {
  rows: ValidationRow[];
  projectAccession: string;
  checklistId: string;
  tsvFile: File | null;
}

export function ConfirmStep({ rows, projectAccession, checklistId, tsvFile }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    samples?: string[];
    experiments?: string[];
    runs?: string[];
    error?: string;
  } | null>(null);

  const handleConfirm = async () => {
    if (!tsvFile) return;
    setConfirming(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", tsvFile);
    formData.append("project_accession", projectAccession);
    formData.append("checklist_id", checklistId);

    try {
      const res = await api.post("/bulk-submit/confirm", formData);
      setResult({
        success: true,
        samples: res.data.samples,
        experiments: res.data.experiments,
        runs: res.data.runs,
      });
    } catch (err) {
      let msg = "Submission failed";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { detail?: unknown } } };
        const detail = axErr.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
        else if (detail && typeof detail === "object" && "message" in detail) {
          msg = (detail as { message: string }).message;
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setResult({ success: false, error: msg });
    }
    setConfirming(false);
  };

  if (result?.success) {
    const samples = result.samples ?? [];
    const experiments = result.experiments ?? [];
    const runs = result.runs ?? [];

    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-green-800 dark:bg-green-950 dark:text-green-200">
          <CheckCircle className="h-5 w-5" />
          <span className="font-semibold">
            Bulk submission complete! {samples.length} sample(s), {experiments.length} experiment(s), {runs.length} run(s) created.
          </span>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Samples</p>
            {samples.map((acc) => (
              <Badge key={acc} variant="outline" className="mr-1 mb-1 text-xs">{acc}</Badge>
            ))}
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Experiments</p>
            {experiments.map((acc) => (
              <Badge key={acc} variant="outline" className="mr-1 mb-1 text-xs">{acc}</Badge>
            ))}
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Runs</p>
            {runs.map((acc) => (
              <Badge key={acc} variant="outline" className="mr-1 mb-1 text-xs">{acc}</Badge>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Confirm Submission</h3>
      <p className="text-sm text-muted-foreground">
        Project: <code className="font-mono">{projectAccession}</code> |
        Checklist: <code className="font-mono">{checklistId}</code> |
        Rows: <strong>{rows.length}</strong>
      </p>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Row</TableHead>
            <TableHead>Sample Alias</TableHead>
            <TableHead>Organism</TableHead>
            <TableHead>Forward File</TableHead>
            <TableHead>Reverse File</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.row_num}>
              <TableCell className="text-muted-foreground">{row.row_num}</TableCell>
              <TableCell className="font-mono text-sm">{row.sample_alias}</TableCell>
              <TableCell className="text-sm">{row.cells?.organism?.value || "—"}</TableCell>
              <TableCell className="text-sm">
                {row.forward_file ? (
                  <span className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    {row.forward_file.filename}
                  </span>
                ) : "—"}
              </TableCell>
              <TableCell className="text-sm">
                {row.reverse_file ? (
                  <span className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    {row.reverse_file.filename}
                  </span>
                ) : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {result?.error && (
        <div className="flex items-center gap-2 rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-200">
          <AlertCircle className="h-4 w-4" />
          <span>{result.error}</span>
        </div>
      )}

      <Button onClick={handleConfirm} disabled={confirming}>
        {confirming ? (
          <>
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            Creating...
          </>
        ) : (
          "Confirm & Create All"
        )}
      </Button>
    </div>
  );
}
