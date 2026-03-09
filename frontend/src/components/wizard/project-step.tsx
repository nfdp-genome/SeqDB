"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface ProjectData {
  title: string;
  description: string;
  project_type: string;
}

interface Props {
  data: ProjectData;
  onChange: (data: ProjectData) => void;
}

const projectTypes = [
  { value: "WGS", label: "Whole Genome Sequencing" },
  { value: "Metagenomics", label: "Metagenomics" },
  { value: "Genotyping", label: "Genotyping" },
  { value: "Transcriptomics", label: "Transcriptomics" },
  { value: "Amplicon", label: "Amplicon" },
  { value: "Other", label: "Other" },
];

export function ProjectStep({ data, onChange }: Props) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Project Information</h3>
      <div className="space-y-2">
        <Label htmlFor="title">Project Title</Label>
        <Input
          id="title"
          value={data.title}
          onChange={(e) => onChange({ ...data, title: e.target.value })}
          placeholder="e.g., Dromedary Camel WGS — Riyadh Region"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          value={data.description}
          onChange={(e) => onChange({ ...data, description: e.target.value })}
          placeholder="Brief description of the project"
        />
      </div>
      <div className="space-y-2">
        <Label>Project Type</Label>
        <Select
          value={data.project_type}
          onValueChange={(v) => onChange({ ...data, project_type: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select project type" />
          </SelectTrigger>
          <SelectContent>
            {projectTypes.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
