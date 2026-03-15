"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Shield, Trash2, KeyRound, UserCheck, UserX, Info } from "lucide-react";

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

function RoleBadge({ role }: { role: string }) {
  const styles: Record<string, string> = {
    admin: "bg-red-100 text-red-800 border-red-200",
    submitter: "bg-blue-100 text-blue-800 border-blue-200",
    viewer: "bg-gray-100 text-gray-800 border-gray-200",
  };
  return (
    <Badge variant="outline" className={styles[role] || ""}>
      {role}
    </Badge>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return active ? (
    <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
      Active
    </Badge>
  ) : (
    <Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
      Inactive
    </Badge>
  );
}

export default function UsersPage() {
  const queryClient = useQueryClient();

  // Create user form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("submitter");
  const [createMessage, setCreateMessage] = useState("");
  const [createError, setCreateError] = useState(false);

  // Role change state
  const [roleChangeUser, setRoleChangeUser] = useState<User | null>(null);
  const [newRole, setNewRole] = useState("");
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);

  // Confirmation dialog state
  const [confirmAction, setConfirmAction] = useState<{
    type: "delete" | "reset-password";
    user: User;
  } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Fetch users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get("/users?page=1&per_page=50").then((r) => r.data),
  });

  const users: User[] = usersData?.items || usersData || [];

  // Create user
  const createUser = useMutation({
    mutationFn: () =>
      api.post("/auth/register", {
        email,
        password,
        full_name: fullName,
        role,
      }),
    onSuccess: () => {
      setCreateMessage(`User ${email} created successfully`);
      setCreateError(false);
      setEmail("");
      setPassword("");
      setFullName("");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: unknown) => {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setCreateMessage(msg || "Failed to create user");
      setCreateError(true);
    },
  });

  // Change role
  const changeRole = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) =>
      api.put(`/users/${userId}/role`, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setRoleDialogOpen(false);
      setRoleChangeUser(null);
    },
  });

  // Toggle active status
  const toggleActive = useMutation({
    mutationFn: ({ userId, activate }: { userId: number; activate: boolean }) =>
      api.put(`/users/${userId}/${activate ? "activate" : "deactivate"}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  // Reset password
  const resetPassword = useMutation({
    mutationFn: (userId: number) => api.post(`/users/${userId}/reset-password`),
    onSuccess: () => {
      setConfirmOpen(false);
      setConfirmAction(null);
    },
  });

  // Delete user
  const deleteUser = useMutation({
    mutationFn: (userId: number) => api.delete(`/users/${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setConfirmOpen(false);
      setConfirmAction(null);
    },
  });

  function handleConfirm() {
    if (!confirmAction) return;
    if (confirmAction.type === "delete") {
      deleteUser.mutate(confirmAction.user.id);
    } else if (confirmAction.type === "reset-password") {
      resetPassword.mutate(confirmAction.user.id);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-6 w-6" />
        <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
      </div>

      {/* OIDC Status Banner */}
      <div className="flex items-start gap-2 rounded-md border bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-950 dark:text-blue-200">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          Single Sign-On is enabled via Keycloak. Users can also sign in with their organizational account.
        </p>
      </div>

      {/* User List Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            All Users
            <Badge variant="secondary" className="ml-2">
              {users.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading users...</p>
          ) : users.length === 0 ? (
            <p className="text-sm text-muted-foreground">No users found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user: User) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell className="text-sm">{user.email}</TableCell>
                    <TableCell>
                      <RoleBadge role={user.role} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge active={user.is_active} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {user.last_login
                        ? new Date(user.last_login).toLocaleDateString()
                        : "Never"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {/* Change Role */}
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Change role"
                          onClick={() => {
                            setRoleChangeUser(user);
                            setNewRole(user.role);
                            setRoleDialogOpen(true);
                          }}
                        >
                          <Shield className="h-3.5 w-3.5" />
                        </Button>

                        {/* Toggle Active */}
                        <Button
                          size="sm"
                          variant="ghost"
                          title={user.is_active ? "Deactivate" : "Activate"}
                          onClick={() =>
                            toggleActive.mutate({
                              userId: user.id,
                              activate: !user.is_active,
                            })
                          }
                        >
                          {user.is_active ? (
                            <UserX className="h-3.5 w-3.5" />
                          ) : (
                            <UserCheck className="h-3.5 w-3.5" />
                          )}
                        </Button>

                        {/* Reset Password */}
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Reset password"
                          onClick={() => {
                            setConfirmAction({ type: "reset-password", user });
                            setConfirmOpen(true);
                          }}
                        >
                          <KeyRound className="h-3.5 w-3.5" />
                        </Button>

                        {/* Delete */}
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Delete user"
                          className="text-destructive hover:text-destructive"
                          onClick={() => {
                            setConfirmAction({ type: "delete", user });
                            setConfirmOpen(true);
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Role Change Dialog */}
      <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Role</DialogTitle>
            <DialogDescription>
              Change the role for {roleChangeUser?.full_name} ({roleChangeUser?.email})
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={newRole} onValueChange={setNewRole}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="submitter">Submitter</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRoleDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (roleChangeUser) {
                  changeRole.mutate({ userId: roleChangeUser.id, role: newRole });
                }
              }}
              disabled={changeRole.isPending}
            >
              {changeRole.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmAction?.type === "delete" ? "Delete User" : "Reset Password"}
            </DialogTitle>
            <DialogDescription>
              {confirmAction?.type === "delete"
                ? `Are you sure you want to delete ${confirmAction.user.email}? This cannot be undone.`
                : `Are you sure you want to reset the password for ${confirmAction?.user.email}?`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={confirmAction?.type === "delete" ? "destructive" : "default"}
              onClick={handleConfirm}
              disabled={deleteUser.isPending || resetPassword.isPending}
            >
              {deleteUser.isPending || resetPassword.isPending
                ? "Processing..."
                : confirmAction?.type === "delete"
                  ? "Delete"
                  : "Reset Password"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create User Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Create New User</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="submitter">Submitter</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            onClick={() => createUser.mutate()}
            disabled={createUser.isPending}
            className="w-full sm:w-auto"
          >
            {createUser.isPending ? "Creating..." : "Create User"}
          </Button>
          {createMessage && (
            <p className={`text-sm ${createError ? "text-red-600" : "text-green-600"}`}>
              {createMessage}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
