"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function OIDCCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-[80vh] items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    }>
      <OIDCCallbackContent />
    </Suspense>
  );
}

function OIDCCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("No authorization code received");
      return;
    }

    async function exchangeCode() {
      try {
        const res = await fetch(
          `${baseURL}/auth/oidc/callback?code=${encodeURIComponent(code!)}`,
        );
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || "SSO authentication failed");
        }
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user", JSON.stringify({
          email: "",
          full_name: "",
          must_change_password: data.must_change_password,
        }));

        if (data.must_change_password) {
          router.push("/change-password");
        } else {
          router.push("/dashboard");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "SSO authentication failed");
      }
    }

    exchangeCode();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Authentication Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-600">{error}</p>
            <a href="/login" className="mt-4 block text-sm text-primary hover:underline">
              Back to Sign In
            </a>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Completing authentication...</span>
      </div>
    </div>
  );
}
