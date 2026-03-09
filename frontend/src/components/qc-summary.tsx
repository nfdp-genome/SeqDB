"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface QCReport {
  tool: string;
  status: string;
  summary: Record<string, number | string>;
  report_path?: string;
}

const statusVariant: Record<string, "default" | "secondary" | "destructive"> = {
  pass: "default",
  warn: "secondary",
  fail: "destructive",
};

export function QCSummary({ reports }: { reports: QCReport[] }) {
  if (reports.length === 0) {
    return <p className="text-muted-foreground">No QC reports available</p>;
  }

  return (
    <div className="space-y-4">
      {reports.map((report, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">{report.tool}</CardTitle>
            <Badge variant={statusVariant[report.status] || "secondary"}>
              {report.status}
            </Badge>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(report.summary).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell className="text-muted-foreground">{key.replace(/_/g, " ")}</TableCell>
                    <TableCell className="font-mono">{String(value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
