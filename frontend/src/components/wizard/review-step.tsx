"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  project: { title: string; description: string; project_type: string };
  sample: { organism: string; tax_id: string; collection_date: string; geographic_location: string; checklist_id: string };
  experiment: { platform: string; instrument_model: string; library_strategy: string; library_source: string; library_layout: string; insert_size: string };
  files: File[];
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b py-1 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value || "—"}</span>
    </div>
  );
}

export function ReviewStep({ project, sample, experiment, files }: Props) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Review Submission</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Project</CardTitle></CardHeader>
          <CardContent>
            <Field label="Title" value={project.title} />
            <Field label="Type" value={project.project_type} />
            <Field label="Description" value={project.description} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Sample</CardTitle></CardHeader>
          <CardContent>
            <Field label="Organism" value={sample.organism} />
            <Field label="Tax ID" value={sample.tax_id} />
            <Field label="Checklist" value={sample.checklist_id} />
            <Field label="Location" value={sample.geographic_location} />
            <Field label="Date" value={sample.collection_date} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Experiment</CardTitle></CardHeader>
          <CardContent>
            <Field label="Platform" value={experiment.platform} />
            <Field label="Instrument" value={experiment.instrument_model} />
            <Field label="Strategy" value={experiment.library_strategy} />
            <Field label="Layout" value={experiment.library_layout} />
            <Field label="Insert Size" value={experiment.insert_size} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Files</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm">{files.length} file(s)</p>
            <ul className="mt-1 space-y-1 text-sm text-muted-foreground">
              {files.map((f, i) => (
                <li key={i} className="font-mono">{f.name}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
