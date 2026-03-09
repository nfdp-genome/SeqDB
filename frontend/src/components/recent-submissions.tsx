"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Submission {
  submission_id: string;
  title: string;
  status: string;
  created_at: string;
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  validated: "default",
  deposited: "outline",
  published: "default",
  failed: "destructive",
};

export function RecentSubmissions({ submissions }: { submissions: Submission[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {submissions.length === 0 ? (
          <TableRow>
            <TableCell colSpan={4} className="text-center text-muted-foreground">
              No submissions yet
            </TableCell>
          </TableRow>
        ) : (
          submissions.map((sub) => (
            <TableRow key={sub.submission_id}>
              <TableCell className="font-mono text-sm">{sub.submission_id}</TableCell>
              <TableCell>{sub.title}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[sub.status] || "secondary"}>
                  {sub.status}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {new Date(sub.created_at).toLocaleDateString()}
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}
