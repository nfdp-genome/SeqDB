"use client";

import { useCallback, useState } from "react";
import { Download, Upload, FileSpreadsheet } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";

interface SampleData {
  organism: string;
  tax_id: string;
  collection_date: string;
  geographic_location: string;
  checklist_id: string;
}

interface Props {
  data: SampleData;
  onChange: (data: SampleData) => void;
  studyAccession?: string;
}

const checklists = [
  { id: "ERC000011", label: "ENA Default" },
  { id: "ERC000020", label: "Pathogen Clinical/Host" },
  { id: "ERC000043", label: "Virus Pathogen" },
  { id: "ERC000055", label: "Farm Animal" },
  { id: "snpchip_livestock", label: "SNP Chip Livestock" },
];

export function SamplesStep({ data, onChange, studyAccession }: Props) {
  const [mode, setMode] = useState<"single" | "template">("single");
  const [uploadResult, setUploadResult] = useState<{
    status: string;
    created?: number;
    errors?: { row: number; field: string; message: string }[];
  } | null>(null);
  const [uploading, setUploading] = useState(false);

  const downloadTemplate = useCallback(async () => {
    if (!data.checklist_id) return;
    const response = await api.get(`/templates/${data.checklist_id}/download`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.checklist_id}_template.tsv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data.checklist_id]);

  const uploadTemplate = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file || !studyAccession || !data.checklist_id) return;
      setUploading(true);
      setUploadResult(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("study_accession", studyAccession);
      formData.append("checklist_id", data.checklist_id);
      try {
        const r = await api.post("/templates/upload", formData);
        setUploadResult(r.data);
      } catch (err) {
        setUploadResult({ status: "error" });
      }
      setUploading(false);
    },
    [studyAccession, data.checklist_id]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sample Registration</h3>
        <div className="flex gap-2">
          <Badge
            variant={mode === "single" ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setMode("single")}
          >
            Single
          </Badge>
          <Badge
            variant={mode === "template" ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setMode("template")}
          >
            Template (Bulk)
          </Badge>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Checklist</Label>
        <Select
          value={data.checklist_id}
          onValueChange={(v) => onChange({ ...data, checklist_id: v })}
        >
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

      {mode === "template" ? (
        <div className="space-y-4 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileSpreadsheet className="h-4 w-4" />
            Register multiple samples using a TSV template
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              size="sm"
              disabled={!data.checklist_id}
              onClick={downloadTemplate}
            >
              <Download className="mr-1 h-4 w-4" />
              Download Template
            </Button>
            <label>
              <Button
                variant="outline"
                size="sm"
                disabled={!data.checklist_id || !studyAccession || uploading}
                asChild
              >
                <span className="cursor-pointer">
                  <Upload className="mr-1 h-4 w-4" />
                  {uploading ? "Uploading..." : "Upload Filled Template"}
                </span>
              </Button>
              <input
                type="file"
                accept=".tsv,.txt,.csv"
                className="hidden"
                onChange={uploadTemplate}
                disabled={!data.checklist_id || !studyAccession}
              />
            </label>
          </div>
          {uploadResult && (
            <div
              className={`rounded-md p-3 text-sm ${
                uploadResult.status === "created"
                  ? "bg-green-50 text-green-800"
                  : "bg-red-50 text-red-800"
              }`}
            >
              {uploadResult.status === "created" ? (
                <p>
                  Successfully created {uploadResult.created} sample(s)
                </p>
              ) : (
                <div>
                  <p className="font-medium">Validation failed:</p>
                  <ul className="mt-1 list-disc pl-4">
                    {uploadResult.errors?.map((err, i) => (
                      <li key={i}>
                        Row {err.row}: {err.field} — {err.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          {!studyAccession && (
            <p className="text-sm text-yellow-600">
              Complete the Project step first to enable template upload
            </p>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="organism">Organism</Label>
            <Input
              id="organism"
              value={data.organism}
              onChange={(e) => onChange({ ...data, organism: e.target.value })}
              placeholder="e.g., Camelus dromedarius"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tax_id">Taxonomy ID</Label>
            <Input
              id="tax_id"
              value={data.tax_id}
              onChange={(e) => onChange({ ...data, tax_id: e.target.value })}
              placeholder="e.g., 9838"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="collection_date">Collection Date</Label>
            <Input
              id="collection_date"
              type="date"
              value={data.collection_date}
              onChange={(e) =>
                onChange({ ...data, collection_date: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="geographic_location">Geographic Location</Label>
            <Input
              id="geographic_location"
              value={data.geographic_location}
              onChange={(e) =>
                onChange({ ...data, geographic_location: e.target.value })
              }
              placeholder="e.g., Saudi Arabia:Riyadh"
            />
          </div>
        </div>
      )}
    </div>
  );
}
