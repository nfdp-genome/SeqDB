"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FlaskConical, Database, FileUp, CheckCircle } from "lucide-react";

interface StatsData {
  projects: number;
  samples: number;
  runs: number;
  submissions: number;
}

export function StatsCards({ data }: { data: StatsData }) {
  const cards = [
    { title: "Projects", value: data.projects, icon: FlaskConical, color: "text-blue-500" },
    { title: "Samples", value: data.samples, icon: Database, color: "text-green-500" },
    { title: "Runs", value: data.runs, icon: FileUp, color: "text-orange-500" },
    { title: "Submissions", value: data.submissions, icon: CheckCircle, color: "text-purple-500" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value.toLocaleString()}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
