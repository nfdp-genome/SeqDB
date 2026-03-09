"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface FairScores {
  findable: number;
  accessible: number;
  interoperable: number;
  reusable: number;
}

function ScoreBar({ label, score, letter }: { label: string; score: number; letter: string }) {
  const color = score >= 80 ? "bg-green-500" : score >= 50 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>
          <span className="font-bold">{letter}</span> — {label}
        </span>
        <span className="font-mono">{score}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

export function FairScore({ scores }: { scores: FairScores }) {
  const overall = Math.round(
    (scores.findable + scores.accessible + scores.interoperable + scores.reusable) / 4
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>FAIR Compliance</CardTitle>
        <Badge variant={overall >= 80 ? "default" : overall >= 50 ? "secondary" : "destructive"}>
          {overall}% Overall
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <ScoreBar label="Findable" score={scores.findable} letter="F" />
        <ScoreBar label="Accessible" score={scores.accessible} letter="A" />
        <ScoreBar label="Interoperable" score={scores.interoperable} letter="I" />
        <ScoreBar label="Reusable" score={scores.reusable} letter="R" />
      </CardContent>
    </Card>
  );
}
