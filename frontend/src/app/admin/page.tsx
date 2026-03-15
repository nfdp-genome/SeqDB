"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, FileOutput, CloudUpload, Settings } from "lucide-react";

const sections = [
  {
    href: "/admin/users",
    title: "User Management",
    description: "Create users, assign roles, manage access",
    icon: Users,
  },
  {
    href: "/admin/ena",
    title: "ENA Submissions",
    description: "Export XML, manage public depositions",
    icon: FileOutput,
  },
  {
    href: "/admin/ncbi",
    title: "NCBI Submissions",
    description: "Submit to NCBI, track accession assignments",
    icon: CloudUpload,
  },
];

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="h-6 w-6" />
        <h2 className="text-3xl font-bold tracking-tight">Admin Panel</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <Link key={section.href} href={section.href}>
            <Card className="transition-colors hover:bg-accent">
              <CardHeader className="flex flex-row items-center gap-3">
                <section.icon className="h-5 w-5 text-primary" />
                <CardTitle className="text-base">{section.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{section.description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
