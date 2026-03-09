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

interface ExperimentData {
  platform: string;
  instrument_model: string;
  library_strategy: string;
  library_source: string;
  library_layout: string;
  insert_size: string;
}

interface Props {
  data: ExperimentData;
  onChange: (data: ExperimentData) => void;
}

const platforms = ["ILLUMINA", "OXFORD_NANOPORE", "PACBIO_SMRT", "SNP_CHIP", "HI_C"];
const strategies = ["WGS", "WXS", "RNA_SEQ", "AMPLICON", "Bisulfite_Seq", "Hi_C", "GENOTYPING"];
const sources = ["GENOMIC", "TRANSCRIPTOMIC", "METAGENOMIC", "VIRAL_RNA"];
const layouts = ["PAIRED", "SINGLE"];

export function ExperimentStep({ data, onChange }: Props) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Experiment Details</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Platform</Label>
          <Select value={data.platform} onValueChange={(v) => onChange({ ...data, platform: v })}>
            <SelectTrigger><SelectValue placeholder="Select platform" /></SelectTrigger>
            <SelectContent>
              {platforms.map((p) => <SelectItem key={p} value={p}>{p.replace("_", " ")}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="instrument_model">Instrument Model</Label>
          <Input
            id="instrument_model"
            value={data.instrument_model}
            onChange={(e) => onChange({ ...data, instrument_model: e.target.value })}
            placeholder="e.g., NovaSeq 6000"
          />
        </div>
        <div className="space-y-2">
          <Label>Library Strategy</Label>
          <Select value={data.library_strategy} onValueChange={(v) => onChange({ ...data, library_strategy: v })}>
            <SelectTrigger><SelectValue placeholder="Select strategy" /></SelectTrigger>
            <SelectContent>
              {strategies.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Library Source</Label>
          <Select value={data.library_source} onValueChange={(v) => onChange({ ...data, library_source: v })}>
            <SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger>
            <SelectContent>
              {sources.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Library Layout</Label>
          <Select value={data.library_layout} onValueChange={(v) => onChange({ ...data, library_layout: v })}>
            <SelectTrigger><SelectValue placeholder="Select layout" /></SelectTrigger>
            <SelectContent>
              {layouts.map((l) => <SelectItem key={l} value={l}>{l}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="insert_size">Insert Size</Label>
          <Input
            id="insert_size"
            type="number"
            value={data.insert_size}
            onChange={(e) => onChange({ ...data, insert_size: e.target.value })}
            placeholder="e.g., 350"
          />
        </div>
      </div>
    </div>
  );
}
