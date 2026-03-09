"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Upload, FileSpreadsheet } from "lucide-react";
import { QuickSubmit } from "@/components/submit/quick-submit";
import { BulkSubmit } from "@/components/submit/bulk-submit";

export default function SubmitPage() {
  const [mode, setMode] = useState<"select" | "quick" | "bulk">("select");

  if (mode === "quick") return <QuickSubmit onBack={() => setMode("select")} />;
  if (mode === "bulk") return <BulkSubmit onBack={() => setMode("select")} />;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Submit Data</h2>
      <p className="text-muted-foreground">Choose a submission method</p>
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="cursor-pointer hover:border-primary transition-colors" onClick={() => setMode("quick")}>
          <CardHeader>
            <Upload className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Quick Submit</CardTitle>
            <CardDescription>Single sample with inline file upload. Best for one-off submissions.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>Create project, sample, experiment</li>
              <li>Upload files directly</li>
              <li>Step-by-step wizard</li>
            </ul>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-primary transition-colors" onClick={() => setMode("bulk")}>
          <CardHeader>
            <FileSpreadsheet className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Bulk Submit</CardTitle>
            <CardDescription>Multiple samples via sample sheet. ENA-style upload-first workflow.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>Upload files to staging (or FTP)</li>
              <li>Fill sample sheet with metadata + checksums</li>
              <li>Auto-link files by MD5 validation</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
