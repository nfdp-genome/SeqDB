"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft } from "lucide-react";
import { ProjectStep } from "@/components/wizard/project-step";
import { SamplesStep } from "@/components/wizard/samples-step";
import { ExperimentStep } from "@/components/wizard/experiment-step";
import { UploadStep } from "@/components/wizard/upload-step";
import { ReviewStep } from "@/components/wizard/review-step";

const steps = ["Project", "Sample", "Experiment", "Upload", "Review"];

interface Props {
  onBack: () => void;
}

export function QuickSubmit({ onBack }: Props) {
  const [step, setStep] = useState(0);
  const [project, setProject] = useState({ title: "", description: "", project_type: "" });
  const [sample, setSample] = useState({
    organism: "", tax_id: "", collection_date: "", geographic_location: "", checklist_id: "",
  });
  const [experiment, setExperiment] = useState({
    platform: "", instrument_model: "", library_strategy: "",
    library_source: "", library_layout: "", insert_size: "",
  });
  const [files, setFiles] = useState<File[]>([]);

  // Accessions created progressively as user advances steps
  const [projectAcc, setProjectAcc] = useState<string | undefined>();
  const [sampleAcc, setSampleAcc] = useState<string | undefined>();
  const [expAcc, setExpAcc] = useState<string | undefined>();
  const [submitted, setSubmitted] = useState(false);
  const [stepError, setStepError] = useState<string | undefined>();

  // Create entities progressively when advancing steps
  async function advanceStep() {
    setStepError(undefined);
    try {
      if (step === 0 && !projectAcc) {
        // Create project when leaving step 0
        if (!project.title || !project.project_type) {
          setStepError("Please fill in Project Title and Project Type");
          return;
        }
        const res = await api.post("/projects", project);
        setProjectAcc(res.data.accession);
      }

      if (step === 1 && !sampleAcc && sample.organism) {
        // Create sample when leaving step 1 (only if single mode was used)
        if (!projectAcc) {
          setStepError("Project not created yet");
          return;
        }
        const res = await api.post("/samples", {
          project_accession: projectAcc,
          checklist_id: sample.checklist_id,
          organism: sample.organism,
          tax_id: parseInt(sample.tax_id),
          collection_date: sample.collection_date,
          geographic_location: sample.geographic_location,
        });
        setSampleAcc(res.data.accession);
      }

      if (step === 2 && !expAcc) {
        if (!sampleAcc) {
          setStepError("No sample created yet. Register a sample first.");
          return;
        }
        if (!experiment.platform || !experiment.library_strategy) {
          setStepError("Please fill in Platform and Library Strategy");
          return;
        }
        const res = await api.post("/experiments", {
          sample_accession: sampleAcc,
          platform: experiment.platform,
          instrument_model: experiment.instrument_model,
          library_strategy: experiment.library_strategy,
          library_source: experiment.library_source,
          library_layout: experiment.library_layout,
          insert_size: parseInt(experiment.insert_size) || 0,
        });
        setExpAcc(res.data.accession);
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

  const submitMutation = useMutation({
    mutationFn: async () => {
      setSubmitted(true);
    },
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back
        </Button>
        <h2 className="text-3xl font-bold tracking-tight">Quick Submit</h2>
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
            {i === 1 && sampleAcc && " \u2713"}
            {i === 2 && expAcc && " \u2713"}
          </Badge>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          {submitted ? (
            <div className="space-y-2 text-center">
              <h3 className="text-lg font-semibold text-green-600">Submission Complete</h3>
              {projectAcc && <p>Project: <code>{projectAcc}</code></p>}
              {sampleAcc && <p>Sample: <code>{sampleAcc}</code></p>}
              {expAcc && <p>Experiment: <code>{expAcc}</code></p>}
            </div>
          ) : (
            <>
              {step === 0 && <ProjectStep data={project} onChange={setProject} />}
              {step === 1 && (
                <SamplesStep
                  data={sample}
                  onChange={setSample}
                  studyAccession={projectAcc}
                />
              )}
              {step === 2 && <ExperimentStep data={experiment} onChange={setExperiment} />}
              {step === 3 && (
                <UploadStep
                  files={files}
                  onChange={setFiles}
                  experimentAccession={expAcc}
                />
              )}
              {step === 4 && <ReviewStep project={project} sample={sample} experiment={experiment} files={files} />}

              {stepError && (
                <p className="mt-3 text-sm text-red-600">{stepError}</p>
              )}

              <div className="mt-6 flex justify-between">
                <Button variant="outline" disabled={step === 0} onClick={() => { setStepError(undefined); setStep(step - 1); }}>
                  Previous
                </Button>
                {step < 4 ? (
                  <Button onClick={advanceStep}>Next</Button>
                ) : (
                  <Button onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending}>
                    {submitMutation.isPending ? "Finalizing..." : "Finish"}
                  </Button>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
