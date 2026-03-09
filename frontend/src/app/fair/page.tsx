"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FairScore } from "@/components/fair-score";
import { AlertTriangle, CheckCircle } from "lucide-react";

export default function FairPage() {
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
  });

  const { data: samples } = useQuery({
    queryKey: ["samples"],
    queryFn: () => api.get("/samples").then((r) => r.data),
  });

  const totalProjects = projects?.length ?? 0;
  const totalSamples = samples?.length ?? 0;
  const samplesWithChecklist = (samples ?? []).filter((s: Record<string, string>) => s.checklist_id).length;
  const samplesWithOrganism = (samples ?? []).filter((s: Record<string, string>) => s.organism).length;
  const projectsWithLicense = (projects ?? []).filter((s: Record<string, string>) => s.license).length;

  const scores = {
    findable: totalProjects > 0 ? 90 : 0,
    accessible: totalProjects > 0 ? 85 : 0,
    interoperable: totalSamples > 0 ? Math.round((samplesWithChecklist / totalSamples) * 100) : 0,
    reusable: totalProjects > 0
      ? Math.round(((projectsWithLicense / totalProjects) * 50 + (samplesWithOrganism / Math.max(totalSamples, 1)) * 50))
      : 0,
  };

  const alerts = [];
  if (totalSamples > 0 && samplesWithChecklist < totalSamples) {
    alerts.push(`${totalSamples - samplesWithChecklist} sample(s) missing checklist assignment`);
  }
  if (totalProjects > 0 && projectsWithLicense < totalProjects) {
    alerts.push(`${totalProjects - projectsWithLicense} project(s) missing license`);
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">FAIR Dashboard</h2>

      <FairScore scores={scores} />

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Compliance Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm">All metadata is compliant</span>
            </div>
          ) : (
            <ul className="space-y-2">
              {alerts.map((alert, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-yellow-600">
                  <AlertTriangle className="h-4 w-4" />
                  {alert}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
