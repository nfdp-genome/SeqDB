"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatsCards } from "@/components/stats-cards";
import { RecentSubmissions } from "@/components/recent-submissions";

export default function DashboardPage() {
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
  });

  const { data: samples } = useQuery({
    queryKey: ["samples"],
    queryFn: () => api.get("/samples").then((r) => r.data),
  });

  const { data: runs } = useQuery({
    queryKey: ["runs"],
    queryFn: () => api.get("/runs").then((r) => r.data),
  });

  const { data: submissions } = useQuery({
    queryKey: ["submissions"],
    queryFn: () => api.get("/submissions").then((r) => r.data),
  });

  const stats = {
    projects: projects?.length ?? 0,
    samples: samples?.length ?? 0,
    runs: runs?.length ?? 0,
    submissions: submissions?.length ?? 0,
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>

      <StatsCards data={stats} />

      <Card>
        <CardHeader>
          <CardTitle>Recent Submissions</CardTitle>
        </CardHeader>
        <CardContent>
          <RecentSubmissions submissions={submissions ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
