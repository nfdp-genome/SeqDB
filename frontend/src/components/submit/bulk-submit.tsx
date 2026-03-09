"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";
import { ProjectStep, type ProjectData } from "@/components/wizard/project-step";
import { StagingUpload } from "@/components/submit/staging-upload";
import { SampleSheetStep } from "@/components/submit/sample-sheet-step";
import { ConfirmStep } from "@/components/submit/confirm-step";

const steps = ["Project", "Upload Files", "Sample Sheet", "Confirm"];

interface ValidationRow {
  row_num: number;
  sample_alias: string;
  cells?: Record<string, { value: string; status: string }>;
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

interface ExistingProject {
  accession: string;
  title: string;
  project_type: string;
}

interface Props {
  onBack: () => void;
}

export function BulkSubmit({ onBack }: Props) {
  const [step, setStep] = useState(0);
  const [stepError, setStepError] = useState<string | undefined>();

  // Step 1: Project
  const [projectMode, setProjectMode] = useState<"new" | "existing">("new");
  const [project, setProject] = useState<ProjectData>({ title: "", description: "", project_type: "" });
  const [projectAcc, setProjectAcc] = useState<string | undefined>();

  // Step 2: Staging
  const [hasStagedFiles, setHasStagedFiles] = useState(false);

  // Step 3: Sample sheet
  const [checklistId, setChecklistId] = useState("");
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [tsvFile, setTsvFile] = useState<File | null>(null);

  // Fetch existing projects for "select existing" mode
  const { data: existingProjects = [] } = useQuery<ExistingProject[]>({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
    enabled: projectMode === "existing",
  });

  const handleStagedFilesChange = useCallback((has: boolean) => {
    setHasStagedFiles(has);
  }, []);

  async function advanceStep() {
    setStepError(undefined);
    try {
      if (step === 0 && !projectAcc) {
        if (projectMode === "new") {
          if (!project.title || !project.project_type) {
            setStepError("Please fill in Project Title and Project Type");
            return;
          }
          const res = await api.post("/projects", project);
          setProjectAcc(res.data.accession);
        } else {
          setStepError("Please select an existing project");
          return;
        }
      }

      // Step 1 (upload) is optional — files may already be staged from a previous session
      // or user may only want to register samples via sample sheet without files

      if (step === 2) {
        if (!validationResult || !validationResult.valid) {
          setStepError("Please upload and validate a sample sheet first");
          return;
        }
      }

      setStep(step + 1);
    } catch (err: unknown) {
      let msg = "Request failed";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { status?: number; data?: { detail?: unknown } } };
        if (axErr.response?.status === 401) {
          msg = "Not authenticated. Please sign in first.";
        } else {
          const detail = axErr.response?.data?.detail;
          if (typeof detail === "string") {
            msg = detail;
          } else if (Array.isArray(detail)) {
            msg = detail.map((e: { loc?: string[]; msg?: string }) =>
              `${(e.loc || []).join(".")}: ${e.msg || "invalid"}`
            ).join("; ");
          }
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setStepError(msg);
    }
  }

  const canAdvance = () => {
    if (step === 0) return projectAcc || (projectMode === "new" && project.title && project.project_type) || projectMode === "existing";
    if (step === 1) return true; // always allow proceeding — files may already be staged
    if (step === 2) return validationResult?.valid === true;
    return false;
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back
        </Button>
        <h2 className="text-3xl font-bold tracking-tight">Bulk Submit</h2>
      </div>

      <div className="flex gap-2">
        {steps.map((s, i) => (
          <Badge
            key={s}
            variant={i === step ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => i < step && setStep(i)}
          >
            {i + 1}. {s}
            {i === 0 && projectAcc && " \u2713"}
            {i === 1 && hasStagedFiles && " \u2713"}
            {i === 2 && validationResult?.valid && " \u2713"}
          </Badge>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          {/* Step 1: Project */}
          {step === 0 && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge
                  variant={projectMode === "new" ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => { setProjectMode("new"); setProjectAcc(undefined); }}
                >
                  Create New
                </Badge>
                <Badge
                  variant={projectMode === "existing" ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => { setProjectMode("existing"); setProjectAcc(undefined); }}
                >
                  Select Existing
                </Badge>
              </div>

              {projectMode === "new" ? (
                projectAcc ? (
                  <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 dark:bg-green-950 dark:text-green-200">
                    Project created: <code>{projectAcc}</code>
                  </div>
                ) : (
                  <ProjectStep data={project} onChange={setProject} />
                )
              ) : (
                <div className="space-y-2">
                  <Label>Existing Project</Label>
                  <Select
                    value={projectAcc || ""}
                    onValueChange={(v) => setProjectAcc(v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a project" />
                    </SelectTrigger>
                    <SelectContent>
                      {existingProjects.map((p) => (
                        <SelectItem key={p.accession} value={p.accession}>
                          {p.accession} — {p.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Upload Files to Staging */}
          {step === 1 && (
            <StagingUpload
              hasStagedFiles={hasStagedFiles}
              onStagedFilesChange={handleStagedFilesChange}
            />
          )}

          {/* Step 3: Sample Sheet */}
          {step === 2 && (
            <SampleSheetStep
              checklistId={checklistId}
              onChecklistChange={setChecklistId}
              validationResult={validationResult}
              onValidationChange={setValidationResult}
              tsvFile={tsvFile}
              onTsvFileChange={setTsvFile}
            />
          )}

          {/* Step 4: Confirm */}
          {step === 3 && projectAcc && (
            <ConfirmStep
              rows={validationResult?.rows ?? []}
              projectAccession={projectAcc}
              checklistId={checklistId}
              tsvFile={tsvFile}
            />
          )}

          {stepError && (
            <p className="mt-3 text-sm text-red-600">{stepError}</p>
          )}

          {step < 3 && (
            <div className="mt-6 flex justify-between">
              <Button
                variant="outline"
                disabled={step === 0}
                onClick={() => { setStepError(undefined); setStep(step - 1); }}
              >
                Previous
              </Button>
              <div className="flex items-center gap-2">
                {step === 1 && !hasStagedFiles && (
                  <span className="text-xs text-muted-foreground">Files already staged? Skip ahead.</span>
                )}
                <Button onClick={advanceStep}>
                  {step === 1 && !hasStagedFiles ? "Skip" : "Next"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
