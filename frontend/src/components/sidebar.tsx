"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Search,
  FileCheck,
  Shield,
  Settings,
  Dna,
  LogIn,
  LogOut,
  User2,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/submit", label: "Submit Data", icon: Upload },
  { href: "/browse", label: "Browse", icon: Search },
  { href: "/fair", label: "FAIR Dashboard", icon: FileCheck },
  { href: "/profile", label: "Profile", icon: User2 },
  { href: "/admin", label: "Admin", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { token, user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card">
      <div className="flex items-center gap-2 border-b px-6 py-4">
        <Dna className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-lg font-bold">SeqDB</h1>
          <p className="text-xs text-muted-foreground">Genomic Data Platform</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t px-3 py-3">
        {token ? (
          <div className="space-y-2">
            <p className="truncate px-3 text-xs text-muted-foreground">
              {user?.email}
            </p>
            <button
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          >
            <LogIn className="h-4 w-4" />
            Sign In
          </Link>
        )}
        <p className="mt-2 px-3 text-xs text-muted-foreground">
          <Shield className="mr-1 inline h-3 w-3" />
          FAIR Compliant
        </p>
      </div>
    </aside>
  );
}
