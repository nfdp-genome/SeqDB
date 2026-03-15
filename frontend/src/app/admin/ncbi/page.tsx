"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  CloudUpload,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  RotateCcw,
} from "lucide-react";

interface ArchiveSubmission {
  id: number;
  submission_id: string;
  archive: string;
  entity_type: string;
  entity_accession: string;
  status: string;
  ncbi_accession?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

function statusIcon(status: string) {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-3.5 w-3.5 text-green-500" />;
    case "failed":
      return <AlertCircle className="h-3.5 w-3.5 text-red-500" />;
    default:
      return <Clock className="h-3.5 w-3.5 text-yellow-500" />;
  }
}

function statusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "completed":
      return "default";
    case "failed":
      return "destructive";
    default:
      return "secondary";
  }
}

export default function NCBIPage() {
  const queryClient = useQueryClient();
  const [retrying, setRetrying] = useState<string | null>(null);

  const { data: submissions = [], isLoading } = useQuery<ArchiveSubmission[]>({
    queryKey: ["ncbi-submissions"],
    queryFn: () =>
      api
        .get("/archive-submissions", { params: { archive: "ncbi" } })
        .then((r) => r.data),
  });

  const retryMutation = useMutation({
    mutationFn: (submissionId: string) =>
      api.post(`/ncbi/retry/${submissionId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ncbi-submissions"] });
      setRetrying(null);
    },
  });

  const ncbiSubs = submissions.filter(
    (s: ArchiveSubmission) => s.archive === "ncbi"
  );

  const pending = ncbiSubs.filter((s) => s.status === "submitted" || s.status === "draft");
  const completed = ncbiSubs.filter((s) => s.status === "completed");
  const failed = ncbiSubs.filter((s) => s.status === "failed");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <CloudUpload className="h-6 w-6" />
        <h2 className="text-3xl font-bold tracking-tight">
          NCBI Submissions
        </h2>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{pending.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">
              {completed.length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">{failed.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Submissions table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">
            All NCBI Submissions
            <Badge variant="secondary" className="ml-2">
              {ncbiSubs.length}
            </Badge>
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ["ncbi-submissions"] })
            }
          >
            <RefreshCw className="mr-1 h-3.5 w-3.5" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : ncbiSubs.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No NCBI submissions yet. Submit a project to NCBI from its detail
              page.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Entity</TableHead>
                  <TableHead>Accession</TableHead>
                  <TableHead>NCBI Accession</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ncbiSubs.map((sub) => (
                  <TableRow key={sub.id}>
                    <TableCell className="text-sm capitalize">
                      {sub.entity_type}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {sub.entity_accession}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {sub.ncbi_accession || (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        {statusIcon(sub.status)}
                        <Badge variant={statusVariant(sub.status)}>
                          {sub.status}
                        </Badge>
                      </div>
                      {sub.error_message && (
                        <p className="mt-1 text-xs text-red-500">
                          {sub.error_message}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(sub.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {sub.status === "failed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={retrying === sub.submission_id}
                          onClick={() => {
                            setRetrying(sub.submission_id);
                            retryMutation.mutate(sub.submission_id);
                          }}
                        >
                          <RotateCcw className="mr-1 h-3 w-3" />
                          Retry
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
