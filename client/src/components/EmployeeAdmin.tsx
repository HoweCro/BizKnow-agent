"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { API_BASE_URL } from "@/lib/api";
import type { Employee } from "./AuthShell";

type Props = { token: string };

const emptyForm = {
  username: "",
  password: "",
  display_name: "",
  department: "",
  job_level: "",
  position: "",
  hire_date: "",
};

export default function EmployeeAdmin({ token }: Props) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");

  async function refreshEmployees() {
    const response = await fetch(`${API_BASE_URL}/employees`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) setEmployees((await response.json()).employees);
  }

  useEffect(() => {
    void refreshEmployees();
  }, [token]);

  async function createEmployee(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    const response = await fetch(`${API_BASE_URL}/employees`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(form),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || "Could not create employee account.");
      return;
    }
    setMessage(`Created account for ${data.user.display_name}.`);
    setForm(emptyForm);
    await refreshEmployees();
  }

  return (
    <section className="mx-auto mt-5 w-full max-w-5xl px-4 md:px-6">
      <details className="glass rounded-2xl p-5">
        <summary className="cursor-pointer font-semibold">Administrator · Employee accounts ({employees.length})</summary>
        <div className="mt-5 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-muted-foreground">Current employees</h2>
            <div className="max-h-64 space-y-2 overflow-y-auto">
              {employees.map((employee) => (
                <div key={employee.id} className="flex flex-wrap justify-between gap-2 rounded-xl border border-border/60 bg-background/50 p-3 text-sm">
                  <span className="font-medium">{employee.display_name} <span className="text-muted-foreground">({employee.username})</span></span>
                  <span className="text-muted-foreground">{employee.department} · {employee.position} · {employee.job_level} · Hired {employee.hire_date}</span>
                </div>
              ))}
            </div>
          </div>
          <form onSubmit={createEmployee} className="grid gap-3 sm:grid-cols-2">
            <h2 className="text-sm font-semibold text-muted-foreground sm:col-span-2">Create employee account</h2>
            {([
              ["username", "Login username"], ["display_name", "Employee name"],
              ["department", "Department"], ["job_level", "Job level"],
              ["position", "Position"],
            ] as const).map(([key, label]) => (
              <label key={key} className="space-y-1 text-xs text-muted-foreground">
                {label}
                <input required value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground" />
              </label>
            ))}
            <label className="space-y-1 text-xs text-muted-foreground">
              Hire date
              <input required type="date" value={form.hire_date} onChange={(event) => setForm({ ...form, hire_date: event.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground" />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
              Temporary password (at least 12 characters)
              <input required minLength={12} type="password" autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground" />
            </label>
            {message && <p role="status" className="text-sm text-muted-foreground sm:col-span-2">{message}</p>}
            <button className="h-10 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground sm:col-span-2">Create account</button>
          </form>
        </div>
      </details>
    </section>
  );
}
