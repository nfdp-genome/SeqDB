"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";

interface AuthState {
  token: string | null;
  user: { email: string; full_name: string } | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ email: string; full_name: string } | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("access_token");
    const savedUser = localStorage.getItem("user");
    if (saved) setToken(saved);
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)); } catch {}
    }
  }, []);

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${baseURL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify({ email, full_name: email }));
    setToken(data.access_token);
    setUser({ email, full_name: email });
  }, [baseURL]);

  const register = useCallback(async (email: string, password: string, full_name: string) => {
    const res = await fetch(`${baseURL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    // Auto-login after register
    await login(email, password);
  }, [baseURL, login]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
