"use client";

import { useQuery } from "@tanstack/react-query";
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
import { FileOutput } from "lucide-react";

export default function ENAPage() {
  const { data: submissions } = useQuery({
    queryKey: ["submissions"],
    queryFn: () => api.get("/submissions").then((r) => r.data),
  });

  const validated = (submissions ?? []).filter(
    (s: Record<string, string>) => s.status === "validated"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <FileOutput className="h-6 w-6" />
        <h2 className="text-3xl font-bold tracking-tight">ENA Submissions</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            Validated Submissions Ready for ENA Export
            <Badge variant="secondary" className="ml-2">{validated.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {validated.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No validated submissions ready for export. Validate submissions first.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Submission ID</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {validated.map((sub: Record<string, string>) => (
                  <TableRow key={sub.submission_id}>
                    <TableCell className="font-mono text-sm">{sub.submission_id}</TableCell>
                    <TableCell>{sub.title}</TableCell>
                    <TableCell>
                      <Badge variant="default">{sub.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline">
                        <FileOutput className="mr-1 h-3 w-3" />
                        Export XML
                      </Button>
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
