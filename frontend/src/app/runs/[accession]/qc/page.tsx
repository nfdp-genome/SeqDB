"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { QCSummary } from "@/components/qc-summary";

export default function QCPage() {
  const params = useParams<{ accession: string }>();

  const { data: reports, isLoading } = useQuery({
    queryKey: ["qc", params.accession],
    queryFn: () => api.get(`/runs/${params.accession}/qc`).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">QC Report</h2>
        <p className="text-muted-foreground font-mono">{params.accession}</p>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading QC reports...</p>
      ) : (
        <QCSummary reports={reports ?? []} />
      )}
    </div>
  );
}
