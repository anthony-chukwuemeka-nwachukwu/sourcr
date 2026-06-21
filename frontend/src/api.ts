// Typed client for the Sourcr FastAPI backend.

export type Confidence = "VERIFIED" | "LIKELY" | "UNVERIFIED" | "CONFLICTING";
export type Overall = "HIGH" | "MEDIUM" | "LOW" | "NEEDS_REVIEW";

export interface FactClaim {
  fact: string;
  confidence: Confidence;
  sources: string[];
}

export interface Contact {
  name: string;
  title: string;
  profile_url?: string | null;
  source_url?: string | null;
}

export interface OpportunityBrief {
  company_name: string;
  website?: string | null;
  domain?: string | null;
  summary: string;
  fit_rationale: string;
  key_facts: FactClaim[];
  decision_makers: Contact[];
  overall_confidence: Overall;
}

export type RunState = "pending" | "running" | "done" | "error";

export interface RunStatus {
  status: RunState;
  briefs: OpportunityBrief[];
  error?: string | null;
}

export interface Options {
  industries: string[];
  ownership_types: string[];
}

export interface Thesis {
  industry: string;
  sub_sector: string;
  geography: string;
  revenue_min?: number | null;
  revenue_max?: number | null;
  employee_min?: number | null;
  employee_max?: number | null;
  ownership_preference: string;
  notes?: string | null;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`Request failed (HTTP ${res.status})`);
  return (await res.json()) as T;
}

export const getOptions = (): Promise<Options> => fetch("/api/options").then(json<Options>);

export const createRun = (thesis: Thesis, max_candidates: number): Promise<{ run_id: string }> =>
  fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thesis, max_candidates }),
  }).then(json<{ run_id: string }>);

export const getRun = (id: string): Promise<RunStatus> =>
  fetch(`/api/runs/${id}`).then(json<RunStatus>);
