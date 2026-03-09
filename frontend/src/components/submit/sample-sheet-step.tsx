"use client";

import { useCallback, useState } from "react";
import { Download, Upload, FileSpreadsheet, CheckCircle, AlertCircle, AlertTriangle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";

const checklists = [
  { id: "ERC000011", label: "ENA Default" },
  { id: "ERC000020", label: "Pathogen Clinical/Host" },
  { id: "ERC000043", label: "Virus Pathogen" },
  { id: "ERC000055", label: "Farm Animal" },
  { id: "snpchip_livestock", label: "SNP Chip Livestock" },
];

interface CellData {
  value: string;
  status: string;
}

interface ValidationRow {
  row_num: number;
  sample_alias: string;
  cells?: Record<string, CellData>;
  errors?: { row?: number; field: string; message: string }[];
  warnings?: { row?: number; field: string; message: string }[];
  forward_file?: { filename: string; md5: string } | null;
  reverse_file?: { filename: string; md5: string } | null;
}

interface ValidationResult {
  valid: boolean;
  total_rows: number;
  matched_files?: number;
  headers?: string[];
  required_fields?: string[];
  rows: ValidationRow[];
  errors?: { row: number; field: string; message: string }[];
}

interface Props {
  checklistId: string;
  onChecklistChange: (id: string) => void;
  validationResult: ValidationResult | null;
  onValidationChange: (result: ValidationResult | null) => void;
  tsvFile: File | null;
  onTsvFileChange: (file: File | null) => void;
}

export function SampleSheetStep({
  checklistId,
  onChecklistChange,
  validationResult,
  onValidationChange,
  tsvFile,
  onTsvFileChange,
}: Props) {
  const [validating, setValidating] = useState(false);

  const downloadTemplate = useCallback(async () => {
    if (!checklistId) return;
    const response = await api.get(`/bulk-submit/template/${checklistId}`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${checklistId}_bulk_template.tsv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [checklistId]);

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file || !checklistId) return;

      onTsvFileChange(file);
      setValidating(true);
      onValidationChange(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("checklist_id", checklistId);

      try {
        const res = await api.post("/bulk-submit/validate", formData);
        onValidationChange(res.data);
      } catch (err) {
        const errorResult: ValidationResult = {
          valid: false,
          total_rows: 0,
          rows: [],
          errors: [{ row: 0, field: "file", message: err instanceof Error ? err.message : "Validation request failed" }],
        };
        onValidationChange(errorResult);
      }
      setValidating(false);
    },
    [checklistId, onTsvFileChange, onValidationChange]
  );

  const requiredFields = new Set(validationResult?.required_fields ?? []);
  const headers = validationResult?.headers ?? [];
  const totalMissing = validationResult?.rows.reduce((acc, row) => {
    if (!row.cells) return acc;
    return acc + Object.values(row.cells).filter((c) => c.status === "missing_required").length;
  }, 0) ?? 0;
  const totalWarnings = validationResult?.rows.reduce((acc, row) => {
    return acc + (row.warnings?.length ?? 0);
  }, 0) ?? 0;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Sample Sheet</h3>

      {/* Checklist selector */}
      <div className="space-y-2">
        <Label>Checklist</Label>
        <Select value={checklistId} onValueChange={onChecklistChange}>
          <SelectTrigger>
            <SelectValue placeholder="Select metadata checklist" />
          </SelectTrigger>
          <SelectContent>
            {checklists.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Instructions */}
      <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50/50 p-3 text-sm dark:border-blue-900 dark:bg-blue-950/30">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
        <div className="text-xs text-muted-foreground space-y-1">
          <p>
            The template includes <strong>2 demo rows</strong> with example data.
            Replace or remove them with your actual sample metadata before uploading.
          </p>
          <p>
            After upload, the preview table highlights:
            <span className="ml-1 inline-block rounded bg-red-100 px-1 text-red-700 dark:bg-red-900/30 dark:text-red-300">red = missing required</span>,
            <span className="ml-1 inline-block rounded bg-yellow-100 px-1 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300">yellow = empty optional</span>,
            <span className="ml-1 inline-block rounded bg-green-100 px-1 text-green-700 dark:bg-green-900/30 dark:text-green-300">green = filled</span>
          </p>
        </div>
      </div>

      {/* Download template & upload */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          size="sm"
          disabled={!checklistId}
          onClick={downloadTemplate}
        >
          <Download className="mr-1 h-4 w-4" />
          Download Template
        </Button>
        <label>
          <Button
            variant="outline"
            size="sm"
            disabled={!checklistId || validating}
            asChild
          >
            <span className="cursor-pointer">
              <Upload className="mr-1 h-4 w-4" />
              {validating ? "Validating..." : "Upload Filled Sheet"}
            </span>
          </Button>
          <input
            type="file"
            accept=".tsv,.txt,.csv"
            className="hidden"
            onChange={handleFileUpload}
            disabled={!checklistId}
          />
        </label>
      </div>

      {tsvFile && (
        <p className="text-sm text-muted-foreground">
          Uploaded: <code>{tsvFile.name}</code>
        </p>
      )}

      {/* Validation result */}
      {validationResult && (
        <div className="space-y-3">
          {/* Summary banner */}
          {validationResult.valid ? (
            <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-800 dark:bg-green-950 dark:text-green-200">
              <CheckCircle className="h-4 w-4" />
              <span>All {validationResult.total_rows} row(s) valid</span>
              {totalWarnings > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {totalWarnings} warning(s)
                </Badge>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-200">
              <AlertCircle className="h-4 w-4" />
              <span>
                Validation failed — {totalMissing} missing required field(s)
              </span>
            </div>
          )}

          {/* Global errors */}
          {validationResult.errors && validationResult.errors.length > 0 && (
            <div className="space-y-1">
              {validationResult.errors.map((err, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-red-600">
                  <AlertCircle className="h-3.5 w-3.5" />
                  Row {err.row}: <code>{err.field}</code> — {err.message}
                </div>
              ))}
            </div>
          )}

          {/* Cell-level preview table */}
          {headers.length > 0 && validationResult.rows.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Sheet Preview</p>
              <div className="overflow-x-auto rounded-md border">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="sticky left-0 z-10 bg-muted/50 px-2 py-1.5 text-left font-medium">Row</th>
                      {headers.map((h) => (
                        <th
                          key={h}
                          className="whitespace-nowrap px-2 py-1.5 text-left font-medium"
                        >
                          {h}
                          {requiredFields.has(h) && (
                            <span className="ml-0.5 text-red-500">*</span>
                          )}
                        </th>
                      ))}
                      <th className="px-2 py-1.5 text-left font-medium">Files</th>
                      <th className="px-2 py-1.5 text-left font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validationResult.rows.map((row) => {
                      const hasErrors = row.errors && row.errors.length > 0;
                      const hasWarnings = row.warnings && row.warnings.length > 0;
                      return (
                        <tr
                          key={row.row_num}
                          className={`border-b ${hasErrors ? "bg-red-50/50 dark:bg-red-950/20" : ""}`}
                        >
                          <td className="sticky left-0 z-10 bg-inherit px-2 py-1 font-mono text-muted-foreground">
                            {row.row_num}
                          </td>
                          {headers.map((h) => {
                            const cell = row.cells?.[h];
                            if (!cell) {
                              return <td key={h} className="px-2 py-1">—</td>;
                            }
                            return (
                              <td
                                key={h}
                                className={`px-2 py-1 ${cellClass(cell.status)}`}
                                title={cellTitle(h, cell)}
                              >
                                {cell.value || (
                                  <span className="italic opacity-50">
                                    {cell.status === "missing_required" ? "REQUIRED" : "—"}
                                  </span>
                                )}
                              </td>
                            );
                          })}
                          <td className="px-2 py-1 space-y-0.5">
                            {row.forward_file ? (
                              <div className="flex items-center gap-1 text-green-600">
                                <CheckCircle className="h-3 w-3" />
                                <span className="truncate max-w-[150px]">{row.forward_file.filename}</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1 text-yellow-600">
                                <AlertTriangle className="h-3 w-3" />
                                <span>No R1</span>
                              </div>
                            )}
                            {row.reverse_file ? (
                              <div className="flex items-center gap-1 text-green-600">
                                <CheckCircle className="h-3 w-3" />
                                <span className="truncate max-w-[150px]">{row.reverse_file.filename}</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <span>No R2</span>
                              </div>
                            )}
                          </td>
                          <td className="px-2 py-1">
                            {hasErrors ? (
                              <Badge variant="destructive" className="text-[10px]">
                                {row.errors!.length} error(s)
                              </Badge>
                            ) : hasWarnings ? (
                              <Badge variant="secondary" className="text-[10px] text-yellow-700">
                                {row.warnings!.length} warn
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-[10px] text-green-600">
                                OK
                              </Badge>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Legend */}
              <div className="flex gap-4 text-[10px] text-muted-foreground">
                <span>
                  <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-red-200 dark:bg-red-900/50" />
                  Missing required
                </span>
                <span>
                  <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-yellow-200 dark:bg-yellow-900/50" />
                  Empty optional
                </span>
                <span>
                  <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-green-100 dark:bg-green-900/30" />
                  Filled
                </span>
                <span>
                  <span className="text-red-500">*</span> Required field
                </span>
              </div>
            </div>
          )}

          {/* Per-row error details */}
          {validationResult.rows.some((r) => r.errors && r.errors.length > 0) && (
            <div className="space-y-1">
              <p className="text-sm font-medium">Error Details</p>
              <div className="max-h-48 overflow-y-auto rounded-md border p-2 space-y-1">
                {validationResult.rows.flatMap((row) =>
                  (row.errors ?? []).map((err, i) => (
                    <div key={`${row.row_num}-${i}`} className="flex items-center gap-2 text-xs text-red-600">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      <span>Row {err.row ?? row.row_num}: <code className="font-mono">{err.field}</code> — {err.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------- Helpers ---------- */

function cellClass(status: string): string {
  switch (status) {
    case "missing_required":
      return "bg-red-100 dark:bg-red-900/30";
    case "empty_optional":
      return "bg-yellow-50 dark:bg-yellow-900/10";
    case "ok":
      return "";
    default:
      return "";
  }
}

function cellTitle(header: string, cell: CellData): string {
  switch (cell.status) {
    case "missing_required":
      return `${header} is required but empty`;
    case "empty_optional":
      return `${header} is optional`;
    default:
      return header;
  }
}
