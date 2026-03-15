"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";

interface UserInfo {
  email: string;
  full_name: string;
  role?: string;
  must_change_password?: boolean;
  last_login?: string;
  created_at?: string;
}

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  login: (email: string, password: string) => Promise<{ must_change_password?: boolean }>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    const saved = localStorage.getItem("access_token");
    const savedUser = localStorage.getItem("user");
    if (saved) setToken(saved);
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)); } catch {}
    }
  }, []);

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
    const userInfo: UserInfo = {
      email,
      full_name: data.full_name || email,
      role: data.role,
      must_change_password: data.must_change_password || false,
    };
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(userInfo));
    setToken(data.access_token);
    setUser(userInfo);
    return { must_change_password: data.must_change_password };
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

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    const currentToken = localStorage.getItem("access_token");
    const res = await fetch(`${baseURL}/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${currentToken}`,
      },
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to change password");
    }
    // Update user state to clear must_change_password
    setUser((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, must_change_password: false };
      localStorage.setItem("user", JSON.stringify(updated));
      return updated;
    });
  }, [baseURL]);

  const refreshUser = useCallback(async () => {
    const currentToken = localStorage.getItem("access_token");
    if (!currentToken) return;
    const res = await fetch(`${baseURL}/auth/me`, {
      headers: { Authorization: `Bearer ${currentToken}` },
    });
    if (!res.ok) return;
    const data = await res.json();
    const userInfo: UserInfo = {
      email: data.email,
      full_name: data.full_name || data.email,
      role: data.role,
      must_change_password: data.must_change_password || false,
      last_login: data.last_login,
      created_at: data.created_at,
    };
    localStorage.setItem("user", JSON.stringify(userInfo));
    setUser(userInfo);
  }, [baseURL]);

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout, changePassword, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
