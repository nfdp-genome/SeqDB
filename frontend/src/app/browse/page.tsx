"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SearchBar } from "@/components/search-bar";

export default function BrowsePage() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState("projects");
  const queryClient = useQueryClient();

  const handleDeleteProject = async (accession: string) => {
    try {
      await api.delete(`/projects/${accession}`);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    } catch {
      // silently fail — user may not own or project has samples
    }
  };

  const { data: searchResults } = useQuery({
    queryKey: ["search", query],
    queryFn: () => api.get(`/search?q=${encodeURIComponent(query)}`).then((r) => r.data),
    enabled: query.length > 0,
  });

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
    enabled: query.length === 0,
  });

  const { data: samples } = useQuery({
    queryKey: ["samples"],
    queryFn: () => api.get("/samples").then((r) => r.data),
    enabled: query.length === 0,
  });

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Browse Data</h2>

      <SearchBar value={query} onChange={setQuery} />

      {query.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Search Results
              <Badge variant="secondary" className="ml-2">
                {searchResults?.total ?? 0}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {searchResults?.results?.length === 0 ? (
              <p className="text-muted-foreground">No results found</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Accession</TableHead>
                    <TableHead>Title / Organism</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResults?.results?.map((r: Record<string, string>, i: number) => (
                    <TableRow key={i}>
                      <TableCell><Badge variant="outline">{r.type}</Badge></TableCell>
                      <TableCell className="font-mono text-sm">{r.accession}</TableCell>
                      <TableCell>{r.title || r.organism}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="projects">Projects</TabsTrigger>
            <TabsTrigger value="samples">Samples</TabsTrigger>
          </TabsList>
          <TabsContent value="projects">
            <Card>
              <CardContent className="pt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Accession</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="w-[60px]" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(projects ?? []).map((s: Record<string, string>) => (
                      <TableRow key={s.accession}>
                        <TableCell className="font-mono text-sm">
                          <Link href={`/projects/${s.accession}`} className="text-primary hover:underline">
                            {s.accession}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <Link href={`/projects/${s.accession}`} className="hover:underline">
                            {s.title}
                          </Link>
                        </TableCell>
                        <TableCell><Badge variant="outline">{s.project_type}</Badge></TableCell>
                        <TableCell>
                          <button
                            onClick={() => handleDeleteProject(s.accession)}
                            className="text-muted-foreground hover:text-destructive"
                            title="Delete project (only if empty)"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="samples">
            <Card>
              <CardContent className="pt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Accession</TableHead>
                      <TableHead>Organism</TableHead>
                      <TableHead>Location</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(samples ?? []).map((s: Record<string, string>) => (
                      <TableRow key={s.accession}>
                        <TableCell className="font-mono text-sm">{s.accession}</TableCell>
                        <TableCell>{s.organism}</TableCell>
                        <TableCell>{s.geographic_location}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
