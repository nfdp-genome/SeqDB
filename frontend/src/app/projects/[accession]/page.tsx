"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Pencil,
  Plus,
  Save,
  X,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Lightbulb,
  FileSpreadsheet,
  Upload,
  Download,
  FileText,
  Copy,
  CloudUpload,
  Loader2,
} from "lucide-react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FairScore } from "@/components/fair-score";

/* ---------- Types ---------- */

interface Project {
  accession: string;
  ena_accession?: string;
  ncbi_accession?: string;
  title: string;
  description: string;
  project_type: string;
  release_date?: string;
  license: string;
  created_at: string;
}

interface NCBIStatus {
  entity_type: string;
  entity_accession: string;
  status: string;
  ncbi_accession?: string;
  submission_id?: string;
}

interface Sample {
  accession: string;
  organism: string;
  tax_id: number;
  breed?: string;
  collection_date: string;
  geographic_location: string;
  checklist_id: string;
  created_at: string;
}

interface FairData {
  scores: { findable: number; accessible: number; interoperable: number; reusable: number };
  checks: Record<string, Record<string, boolean>>;
  suggestions: string[];
  counts: { samples: number; experiments: number; runs: number };
}

interface FileEntry {
  run_accession: string;
  experiment_accession: string;
  sample_accession: string;
  organism: string;
  file_type: string;
  filename: string;
  file_path: string;
  file_size: number;
  checksum_md5: string;
  download_url: string;
  platform: string;
  instrument_model: string;
  library_strategy: string;
  library_layout: string;
}

/* ---------- Page ---------- */

export default function ProjectDetailPage() {
  const { accession } = useParams<{ accession: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: ["project", accession],
    queryFn: () => api.get(`/projects/${accession}`).then((r) => r.data),
  });

  const { data: samples = [] } = useQuery<Sample[]>({
    queryKey: ["project-samples", accession],
    queryFn: () => api.get(`/samples?project_accession=${accession}`).then((r) => r.data),
  });

  const { data: fair } = useQuery<FairData>({
    queryKey: ["project-fair", accession],
    queryFn: () => api.get(`/projects/${accession}/fair`).then((r) => r.data),
  });

  const { data: files = [] } = useQuery<FileEntry[]>({
    queryKey: ["project-files", accession],
    queryFn: () => api.get(`/filereport?accession=${accession}`).then((r) => r.data),
  });

  const { data: ncbiStatus } = useQuery<NCBIStatus[]>({
    queryKey: ["project-ncbi", accession],
    queryFn: () => api.get(`/ncbi/status/${accession}`).then((r) => r.data),
  });

  if (isLoading) return <p className="p-6 text-muted-foreground">Loading...</p>;
  if (!project) return <p className="p-6 text-red-500">Project not found</p>;

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["project", accession] });
    queryClient.invalidateQueries({ queryKey: ["project-fair", accession] });
    queryClient.invalidateQueries({ queryKey: ["project-samples", accession] });
    queryClient.invalidateQueries({ queryKey: ["project-files", accession] });
    queryClient.invalidateQueries({ queryKey: ["project-ncbi", accession] });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => router.push("/browse")}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          Browse
        </Button>
        <div className="flex-1">
          <h2 className="text-2xl font-bold">{project.title}</h2>
          <p className="text-sm text-muted-foreground">
            <code>{project.accession}</code>
            <Badge variant="outline" className="ml-2">{project.project_type}</Badge>
            <span className="ml-2">License: {project.license}</span>
          </p>
        </div>
      </div>

      {/* FAIR Score */}
      {fair && (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="md:col-span-2">
            <FairScore scores={fair.scores} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Lightbulb className="h-4 w-4" />
                Improve FAIR Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              {fair.suggestions.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  Fully FAIR compliant
                </div>
              ) : (
                <ul className="space-y-2">
                  {fair.suggestions.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-yellow-500" />
                      {s}
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-muted-foreground">
                <div>
                  <p className="text-lg font-bold text-foreground">{fair.counts.samples}</p>
                  Samples
                </div>
                <div>
                  <p className="text-lg font-bold text-foreground">{fair.counts.experiments}</p>
                  Experiments
                </div>
                <div>
                  <p className="text-lg font-bold text-foreground">{fair.counts.runs}</p>
                  Runs
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Project Details - Editable */}
      <ProjectEditCard project={project} onSaved={invalidate} />

      {/* Samples */}
      <SamplesCard
        samples={samples}
        projectAccession={accession}
        onChanged={invalidate}
      />

      {/* Files (ENA-style file report) */}
      {files.length > 0 && (
        <FilesCard files={files} projectAccession={accession} />
      )}

      {/* NCBI Submission */}
      <NCBICard
        projectAccession={accession}
        ncbiAccession={project.ncbi_accession}
        ncbiStatus={ncbiStatus}
        onSubmitted={invalidate}
      />
    </div>
  );
}

/* ---------- Project Edit Card ---------- */

function ProjectEditCard({ project, onSaved }: { project: Project; onSaved: () => void }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(project.title);
  const [description, setDescription] = useState(project.description);
  const [releaseDate, setReleaseDate] = useState(project.release_date || "");
  const [license, setLicense] = useState(project.license);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await api.put(`/projects/${project.accession}`, {
        title,
        description,
        release_date: releaseDate || null,
        license,
      });
      setEditing(false);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const cancel = () => {
    setTitle(project.title);
    setDescription(project.description);
    setReleaseDate(project.release_date || "");
    setLicense(project.license);
    setEditing(false);
    setError("");
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm">Project Details</CardTitle>
        {!editing ? (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="mr-1 h-3.5 w-3.5" />
            Edit
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={cancel}>
              <X className="mr-1 h-3.5 w-3.5" />
              Cancel
            </Button>
            <Button size="sm" onClick={save} disabled={saving}>
              <Save className="mr-1 h-3.5 w-3.5" />
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {editing ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Title</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>License</Label>
              <Select value={license} onValueChange={setLicense}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CC-BY">CC-BY</SelectItem>
                  <SelectItem value="CC-BY-SA">CC-BY-SA</SelectItem>
                  <SelectItem value="CC-BY-NC">CC-BY-NC</SelectItem>
                  <SelectItem value="CC0">CC0 (Public Domain)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Description</Label>
              <textarea
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Release Date</Label>
              <Input type="date" value={releaseDate} onChange={(e) => setReleaseDate(e.target.value)} />
            </div>
            {error && <p className="text-sm text-red-500 md:col-span-2">{error}</p>}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs text-muted-foreground">Title</p>
              <p className="text-sm">{project.title}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">License</p>
              <p className="text-sm">{project.license}</p>
            </div>
            <div className="md:col-span-2">
              <p className="text-xs text-muted-foreground">Description</p>
              <p className="text-sm">{project.description || <span className="italic text-muted-foreground">No description</span>}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Release Date</p>
              <p className="text-sm">{project.release_date || <span className="italic text-muted-foreground">Not set</span>}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Created</p>
              <p className="text-sm">{new Date(project.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ---------- Samples Card with Single + Bulk tabs ---------- */

function SamplesCard({
  samples,
  projectAccession,
  onChanged,
}: {
  samples: Sample[];
  projectAccession: string;
  onChanged: () => void;
}) {
  const [addMode, setAddMode] = useState<null | "single" | "bulk">(null);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm">
          Samples
          <Badge variant="secondary" className="ml-2">{samples.length}</Badge>
        </CardTitle>
        {!addMode && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setAddMode("single")}>
              <Plus className="mr-1 h-3.5 w-3.5" />
              Add Sample
            </Button>
            <Button variant="outline" size="sm" onClick={() => setAddMode("bulk")}>
              <FileSpreadsheet className="mr-1 h-3.5 w-3.5" />
              Bulk Upload
            </Button>
          </div>
        )}
        {addMode && (
          <Button variant="ghost" size="sm" onClick={() => setAddMode(null)}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {samples.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Accession</TableHead>
                <TableHead>Organism</TableHead>
                <TableHead>Breed</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Checklist</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {samples.map((s) => (
                <TableRow key={s.accession}>
                  <TableCell className="font-mono text-xs">{s.accession}</TableCell>
                  <TableCell className="text-sm">{s.organism}</TableCell>
                  <TableCell className="text-sm">{s.breed || "—"}</TableCell>
                  <TableCell className="text-sm">{s.geographic_location}</TableCell>
                  <TableCell className="text-sm">{s.collection_date}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">{s.checklist_id}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        {addMode === "single" && (
          <AddSampleForm
            projectAccession={projectAccession}
            onAdded={() => { onChanged(); }}
          />
        )}

        {addMode === "bulk" && (
          <BulkSampleUpload
            projectAccession={projectAccession}
            onDone={() => { setAddMode(null); onChanged(); }}
          />
        )}
      </CardContent>
    </Card>
  );
}

/* ---------- Add Single Sample Form ---------- */

function AddSampleForm({ projectAccession, onAdded }: { projectAccession: string; onAdded: () => void }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    organism: "",
    tax_id: "",
    collection_date: "",
    geographic_location: "",
    breed: "",
    host: "",
    tissue: "",
    sex: "",
    checklist_id: "ERC000011",
  });

  const set = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  const submit = async () => {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const res = await api.post("/samples", {
        project_accession: projectAccession,
        checklist_id: form.checklist_id,
        organism: form.organism,
        tax_id: parseInt(form.tax_id),
        collection_date: form.collection_date,
        geographic_location: form.geographic_location,
        breed: form.breed || undefined,
        host: form.host || undefined,
        tissue: form.tissue || undefined,
        sex: form.sex || undefined,
      });
      setSuccess(`Sample created: ${res.data.accession}`);
      setForm({
        organism: form.organism,
        tax_id: form.tax_id,
        collection_date: "",
        geographic_location: form.geographic_location,
        breed: form.breed,
        host: form.host,
        tissue: form.tissue,
        sex: form.sex,
        checklist_id: form.checklist_id,
      });
      onAdded();
    } catch (err) {
      let msg = "Failed to create sample";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { detail?: unknown } } };
        const detail = axErr.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
        else if (Array.isArray(detail)) {
          msg = detail.map((e: { loc?: string[]; msg?: string }) =>
            `${(e.loc || []).join(".")}: ${e.msg || "invalid"}`
          ).join("; ");
        }
      }
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border p-4 space-y-4">
      <h4 className="text-sm font-semibold">New Sample</h4>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="space-y-1">
          <Label className="text-xs">Organism *</Label>
          <Input placeholder="Camelus dromedarius" value={form.organism} onChange={(e) => set("organism", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Tax ID *</Label>
          <Input type="number" placeholder="9838" value={form.tax_id} onChange={(e) => set("tax_id", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Collection Date *</Label>
          <Input type="date" value={form.collection_date} onChange={(e) => set("collection_date", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Geographic Location *</Label>
          <Input placeholder="Saudi Arabia" value={form.geographic_location} onChange={(e) => set("geographic_location", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Breed</Label>
          <Input placeholder="Arabian" value={form.breed} onChange={(e) => set("breed", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Host</Label>
          <Input placeholder="Camelus dromedarius" value={form.host} onChange={(e) => set("host", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Tissue</Label>
          <Input placeholder="blood" value={form.tissue} onChange={(e) => set("tissue", e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Sex</Label>
          <Select value={form.sex} onValueChange={(v) => set("sex", v)}>
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="unknown">Unknown</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Checklist</Label>
          <Select value={form.checklist_id} onValueChange={(v) => set("checklist_id", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ERC000011">ERC000011 (ENA default)</SelectItem>
              <SelectItem value="ERC000013">ERC000013 (Viral)</SelectItem>
              <SelectItem value="ERC000020">ERC000020 (Pathogen)</SelectItem>
              <SelectItem value="ERC000043">ERC000043 (Livestock)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      <Button size="sm" onClick={submit} disabled={saving || !form.organism || !form.tax_id || !form.collection_date || !form.geographic_location}>
        {saving ? "Creating..." : "Create Sample"}
      </Button>
    </div>
  );
}

/* ---------- NCBI Submission Card ---------- */

function NCBICard({
  projectAccession,
  ncbiAccession,
  ncbiStatus,
  onSubmitted,
}: {
  projectAccession: string;
  ncbiAccession?: string;
  ncbiStatus?: NCBIStatus[];
  onSubmitted: () => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      await api.post(`/ncbi/submit/${projectAccession}`);
      setSuccess("Submitted to NCBI. Accessions will be assigned automatically.");
      onSubmitted();
    } catch (err) {
      let msg = "NCBI submission failed";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { detail?: unknown } } };
        const detail = axErr.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
      }
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const hasSubmissions = ncbiStatus && ncbiStatus.length > 0;
  const allCompleted = hasSubmissions && ncbiStatus.every((s) => s.status === "completed");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-sm">
          <CloudUpload className="h-4 w-4" />
          NCBI Submission
          {ncbiAccession && (
            <Badge variant="outline" className="ml-1 font-mono text-xs">
              {ncbiAccession}
            </Badge>
          )}
        </CardTitle>
        {!allCompleted && (
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <CloudUpload className="mr-1 h-3.5 w-3.5" />
                {hasSubmissions ? "Resubmit to NCBI" : "Submit to NCBI"}
              </>
            )}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <div className="flex items-center gap-2 text-sm text-red-500">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle className="h-4 w-4" />
            {success}
          </div>
        )}

        {!hasSubmissions ? (
          <p className="text-sm text-muted-foreground">
            No NCBI submissions for this project. Click &quot;Submit to NCBI&quot; to deposit
            the project, samples, and experiments to NCBI.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entity</TableHead>
                <TableHead>Accession</TableHead>
                <TableHead>NCBI Accession</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ncbiStatus!.map((s, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm capitalize">{s.entity_type}</TableCell>
                  <TableCell className="font-mono text-xs">{s.entity_accession}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {s.ncbi_accession || <span className="text-muted-foreground">—</span>}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        s.status === "completed"
                          ? "default"
                          : s.status === "failed"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {s.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

/* ---------- Files Card (ENA-style) ---------- */

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function FilesCard({ files, projectAccession }: { files: FileEntry[]; projectAccession: string }) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const apiUrl = `/api/v1/filereport?accession=${projectAccession}`;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileText className="h-4 w-4" />
          Files
          <Badge variant="secondary">{files.length}</Badge>
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => copyToClipboard(apiUrl, "api")}
          >
            <Copy className="mr-1 h-3.5 w-3.5" />
            {copied === "api" ? "Copied!" : "Copy API URL"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* API hint */}
        <div className="rounded-md border border-blue-200 bg-blue-50/50 p-3 text-xs dark:border-blue-900 dark:bg-blue-950/30 space-y-1">
          <p className="font-medium text-blue-700 dark:text-blue-300">Programmatic Access (ENA-style API)</p>
          <code className="block bg-blue-100 dark:bg-blue-900/40 rounded px-2 py-1 text-[11px] font-mono break-all">
            GET {apiUrl}
          </code>
          <p className="text-muted-foreground">
            Query by any accession: project, sample, experiment, or run. Returns JSON file report with download URLs.
          </p>
          <p className="text-muted-foreground">
            Example: <code className="bg-blue-100 dark:bg-blue-900/40 rounded px-1">curl {apiUrl}</code>
          </p>
        </div>

        {/* File table */}
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Sample</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>MD5</TableHead>
                <TableHead>Platform</TableHead>
                <TableHead className="text-right">Download</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {files.map((f) => (
                <TableRow key={f.run_accession}>
                  <TableCell className="font-mono text-xs max-w-[200px] truncate" title={f.filename}>
                    {f.filename}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{f.sample_accession}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-[10px]">{f.file_type}</Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatBytes(f.file_size)}</TableCell>
                  <TableCell>
                    <button
                      className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground hover:text-foreground"
                      onClick={() => copyToClipboard(f.checksum_md5, f.run_accession)}
                      title="Click to copy MD5"
                    >
                      {f.checksum_md5.slice(0, 12)}...
                      {copied === f.run_accession ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  </TableCell>
                  <TableCell className="text-xs">{f.platform}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                    >
                      <a href={`/api/v1/runs/${f.run_accession}/download`} target="_blank" rel="noopener">
                        <Download className="mr-1 h-3.5 w-3.5" />
                        Download
                      </a>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

/* ---------- Bulk Sample Upload (reuses sample sheet + staging) ---------- */

interface BulkValidationRow {
  row_num: number;
  sample_alias: string;
  cells?: Record<string, { value: string; status: string }>;
  errors?: { field: string; message: string }[];
  forward_file?: { filename: string } | null;
  reverse_file?: { filename: string } | null;
}

interface BulkValidationResult {
  valid: boolean;
  total_rows: number;
  headers?: string[];
  required_fields?: string[];
  rows: BulkValidationRow[];
  errors?: { row: number; field: string; message: string }[];
}

const CHECKLISTS = [
  { id: "ERC000011", label: "ENA Default" },
  { id: "ERC000020", label: "Pathogen Clinical/Host" },
  { id: "ERC000043", label: "Virus Pathogen" },
  { id: "ERC000055", label: "Farm Animal" },
  { id: "snpchip_livestock", label: "SNP Chip Livestock" },
];

function BulkSampleUpload({
  projectAccession,
  onDone,
}: {
  projectAccession: string;
  onDone: () => void;
}) {
  const [checklistId, setChecklistId] = useState("ERC000011");
  const [tsvFile, setTsvFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<BulkValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<{ samples: string[]; experiments: string[]; runs: string[] } | null>(null);
  const [error, setError] = useState("");

  const downloadTemplate = async () => {
    const response = await api.get(`/bulk-submit/template/${checklistId}`, { responseType: "blob" });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${checklistId}_bulk_template.tsv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setTsvFile(file);
    setValidating(true);
    setValidationResult(null);
    setError("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("checklist_id", checklistId);

    try {
      const res = await api.post("/bulk-submit/validate", formData);
      setValidationResult(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    }
    setValidating(false);
  };

  const handleConfirm = async () => {
    if (!tsvFile) return;
    setConfirming(true);
    setError("");

    const formData = new FormData();
    formData.append("file", tsvFile);
    formData.append("project_accession", projectAccession);
    formData.append("checklist_id", checklistId);

    try {
      const res = await api.post("/bulk-submit/confirm", formData);
      setResult(res.data);
    } catch (err) {
      let msg = "Submission failed";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { detail?: unknown } } };
        const detail = axErr.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
        else if (detail && typeof detail === "object" && "message" in detail) {
          msg = (detail as { message: string }).message;
        }
      }
      setError(msg);
    }
    setConfirming(false);
  };

  if (result) {
    return (
      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex items-center gap-2 text-green-600">
          <CheckCircle className="h-5 w-5" />
          <span className="font-semibold text-sm">
            Created {result.samples.length} sample(s), {result.experiments.length} experiment(s), {result.runs.length} run(s)
          </span>
        </div>
        <div className="flex flex-wrap gap-1">
          {result.samples.map((acc) => (
            <Badge key={acc} variant="outline" className="text-xs">{acc}</Badge>
          ))}
        </div>
        <Button size="sm" onClick={onDone}>Done</Button>
      </div>
    );
  }

  const requiredFields = new Set(validationResult?.required_fields ?? []);
  const headers = validationResult?.headers ?? [];

  return (
    <div className="rounded-lg border p-4 space-y-4">
      <h4 className="text-sm font-semibold">Bulk Sample Upload</h4>
      <p className="text-xs text-muted-foreground">
        Download a template, fill it with sample metadata, then upload it. Samples will be added to project <code>{projectAccession}</code>.
      </p>

      {/* Checklist + actions */}
      <div className="flex items-end gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Checklist</Label>
          <Select value={checklistId} onValueChange={setChecklistId}>
            <SelectTrigger className="w-[220px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CHECKLISTS.map((c) => (
                <SelectItem key={c.id} value={c.id}>{c.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" size="sm" onClick={downloadTemplate}>
          <Upload className="mr-1 h-3.5 w-3.5" />
          Download Template
        </Button>
        <label>
          <Button variant="outline" size="sm" disabled={validating} asChild>
            <span className="cursor-pointer">
              <FileSpreadsheet className="mr-1 h-3.5 w-3.5" />
              {validating ? "Validating..." : "Upload Sheet"}
            </span>
          </Button>
          <input type="file" accept=".tsv,.txt,.csv" className="hidden" onChange={handleUpload} />
        </label>
      </div>

      {tsvFile && <p className="text-xs text-muted-foreground">File: <code>{tsvFile.name}</code></p>}

      {/* Validation preview */}
      {validationResult && headers.length > 0 && (
        <div className="space-y-2">
          {validationResult.valid ? (
            <div className="flex items-center gap-2 rounded-md bg-green-50 p-2 text-xs text-green-700 dark:bg-green-950 dark:text-green-200">
              <CheckCircle className="h-3.5 w-3.5" />
              All {validationResult.total_rows} row(s) valid
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-md bg-red-50 p-2 text-xs text-red-700 dark:bg-red-950 dark:text-red-200">
              <AlertCircle className="h-3.5 w-3.5" />
              Validation failed
            </div>
          )}

          <div className="overflow-x-auto rounded-md border max-h-64">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-muted/80 backdrop-blur">
                <tr className="border-b">
                  <th className="px-2 py-1 text-left font-medium">#</th>
                  {headers.map((h) => (
                    <th key={h} className="whitespace-nowrap px-2 py-1 text-left font-medium">
                      {h}{requiredFields.has(h) && <span className="text-red-500">*</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {validationResult.rows.map((row) => (
                  <tr key={row.row_num} className={`border-b ${row.errors && row.errors.length > 0 ? "bg-red-50/50 dark:bg-red-950/20" : ""}`}>
                    <td className="px-2 py-1 text-muted-foreground">{row.row_num}</td>
                    {headers.map((h) => {
                      const cell = row.cells?.[h];
                      if (!cell) return <td key={h} className="px-2 py-1">—</td>;
                      const bg =
                        cell.status === "missing_required" ? "bg-red-100 dark:bg-red-900/30" :
                        cell.status === "empty_optional" ? "bg-yellow-50 dark:bg-yellow-900/10" : "";
                      return (
                        <td key={h} className={`px-2 py-1 ${bg}`}>
                          {cell.value || (cell.status === "missing_required" ? <span className="italic text-red-400">REQUIRED</span> : "—")}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {validationResult?.valid && (
        <Button size="sm" onClick={handleConfirm} disabled={confirming}>
          {confirming ? "Creating..." : `Confirm & Create ${validationResult.total_rows} Sample(s)`}
        </Button>
      )}
    </div>
  );
}
