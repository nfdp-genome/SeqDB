"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setDevToken(null);
    setLoading(true);

    try {
      const res = await fetch(`${baseURL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }

      setSuccess(true);

      // In dev mode, show the reset token for testing
      if (data.reset_token) {
        setDevToken(data.reset_token);
      }
    } catch (err) {
      // Always show success to avoid email enumeration, but show actual errors for non-404
      setSuccess(true);
    }
    setLoading(false);
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Forgot Password</CardTitle>
        </CardHeader>
        <CardContent>
          {success ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                If the email exists, a reset link has been sent.
              </p>
              {devToken && (
                <div className="rounded-md border bg-muted p-3">
                  <p className="text-xs font-medium text-muted-foreground">Dev Mode - Reset Token:</p>
                  <p className="mt-1 break-all font-mono text-xs">{devToken}</p>
                  <Link
                    href={`/reset-password?token=${devToken}`}
                    className="mt-2 block text-xs text-primary hover:underline"
                  >
                    Go to reset page
                  </Link>
                </div>
              )}
              <Link href="/login" className="block text-center text-sm text-primary hover:underline">
                Back to Sign In
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@nfdp.sa"
                  required
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Sending..." : "Send Reset Link"}
              </Button>
              <Link href="/login" className="block text-center text-sm text-primary hover:underline">
                Back to Sign In
              </Link>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
