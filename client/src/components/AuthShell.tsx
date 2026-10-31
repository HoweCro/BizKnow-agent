"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import Chat from "./Chat";
import EmployeeAdmin from "./EmployeeAdmin";
import { API_BASE_URL } from "@/lib/api";

export type Employee = {
  id: number;
  username: string;
  display_name: string;
  department: string;
  job_level: string;
  position: string;
  hire_date: string;
  role: "admin" | "employee";
};

export default function AuthShell() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState<Employee | null>(null);
  const [ready, setReady] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const savedToken = sessionStorage.getItem("employeeToken");
    if (!savedToken) {
      setReady(true);
      return;
    }
    fetch(`${API_BASE_URL}/auth/me`, { headers: { Authorization: `Bearer ${savedToken}` } })
      .then(async (res) => {
        if (!res.ok) throw new Error("Your session expired. Please sign in again.");
        const data = await res.json();
        setToken(savedToken);
        setUser(data.user);
      })
      .catch(() => sessionStorage.removeItem("employeeToken"))
      .finally(() => setReady(true));
  }, []);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to sign in.");
      sessionStorage.setItem("employeeToken", data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to connect to the server.");
    } finally {
      setSubmitting(false);
    }
  }

  function logout() {
    sessionStorage.removeItem("employeeToken");
    setToken("");
    setUser(null);
  }

  if (!ready) {
    return <main className="flex min-h-screen items-center justify-center text-muted-foreground">Loading employee account…</main>;
  }

  if (!token || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center p-5">
        <form onSubmit={handleLogin} className="glass w-full max-w-md space-y-5 rounded-3xl p-8 shadow-2xl">
          <div className="space-y-2 text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Internal knowledge assistant</p>
            <h1 className="text-3xl font-bold">Employee sign in</h1>
            <p className="text-sm text-muted-foreground">Use the account provided by your administrator.</p>
          </div>
          <label className="block space-y-2 text-sm font-medium">
            Login username
            <input autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} className="h-11 w-full rounded-xl border border-border bg-background/70 px-4" />
          </label>
          <label className="block space-y-2 text-sm font-medium">
            Password
            <input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="h-11 w-full rounded-xl border border-border bg-background/70 px-4" />
          </label>
          {error && <p role="alert" className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
          <button disabled={submitting} className="h-11 w-full rounded-xl bg-primary px-4 font-semibold text-primary-foreground disabled:opacity-60">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </main>
    );
  }

  return (
    <>
      {user.role === "admin" && <EmployeeAdmin token={token} />}
      <Chat token={token} user={user} onLogout={logout} />
    </>
  );
}
