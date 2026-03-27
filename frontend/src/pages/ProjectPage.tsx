import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../hooks/useAuth";
import type { JobCreatePayload, JobType } from "../types/api";

export function ProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, signInWithGoogle } = useAuth();
  const [jobForm, setJobForm] = useState<JobCreatePayload>({
    job_type: "full_render",
    requested_duration_minutes: 8,
    diagnostics_mode: false,
    image_generation_enabled: true,
    llm_provider: "heuristic",
    tts_provider: "auto",
    preview_only: false,
  });

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: Boolean(projectId && isAuthenticated),
  });

  const createJob = useMutation({
    mutationFn: (payload: JobCreatePayload) => api.createJob(projectId!, payload),
    onSuccess(job) {
      navigate(`/jobs/${job.id}`);
    },
  });

  if (!isAuthenticated) {
    return (
      <section className="panel panel--empty">
        <h1>Sign in to access this project</h1>
        <button className="button" onClick={() => void signInWithGoogle()} type="button">
          Sign in with Google
        </button>
      </section>
    );
  }

  if (projectQuery.isLoading) {
    return <section className="panel">Loading project...</section>;
  }

  if (!projectQuery.data) {
    return <section className="panel panel--empty">Project not found.</section>;
  }

  const project = projectQuery.data;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Project</span>
          <h1>{project.title}</h1>
        </div>
        <StatusBadge label={project.status} />
      </div>

      <div className="detail-grid">
        <article className="panel">
          <h2>Prompt</h2>
          <p className="long-copy">{project.prompt}</p>
          <div className="tag-row">
            <span>{project.visual_style.replace(/_/g, " ")}</span>
            <span>{project.requested_duration_minutes} min</span>
            <span>{project.topic_domain ?? "general explainer"}</span>
          </div>
        </article>

        <form
          className="panel"
          onSubmit={(event) => {
            event.preventDefault();
            createJob.mutate(jobForm);
          }}
        >
          <h2>Start a render job</h2>
          <div className="form-grid">
            <label className="field">
              <span>Job type</span>
              <select
                value={jobForm.job_type}
                onChange={(event) =>
                  setJobForm((current) => ({
                    ...current,
                    job_type: event.target.value as JobType,
                  }))
                }
              >
                <option value="full_render">Full render</option>
                <option value="preview">Preview</option>
              </select>
            </label>

            <label className="field">
              <span>Duration override</span>
              <input
                type="number"
                min={1}
                max={30}
                value={jobForm.requested_duration_minutes}
                onChange={(event) =>
                  setJobForm((current) => ({
                    ...current,
                    requested_duration_minutes: Number(event.target.value),
                  }))
                }
              />
            </label>

            <label className="field">
              <span>LLM provider</span>
              <select
                value={jobForm.llm_provider}
                onChange={(event) =>
                  setJobForm((current) => ({ ...current, llm_provider: event.target.value }))
                }
              >
                <option value="heuristic">heuristic</option>
                <option value="openrouter">openrouter</option>
                <option value="gemini">gemini</option>
              </select>
            </label>

            <label className="field">
              <span>TTS provider</span>
              <select
                value={jobForm.tts_provider}
                onChange={(event) =>
                  setJobForm((current) => ({ ...current, tts_provider: event.target.value }))
                }
              >
                <option value="auto">auto</option>
                <option value="dummy">dummy</option>
                <option value="piper">piper</option>
              </select>
            </label>

            <label className="field field--checkbox">
              <input
                checked={jobForm.image_generation_enabled}
                onChange={(event) =>
                  setJobForm((current) => ({
                    ...current,
                    image_generation_enabled: event.target.checked,
                  }))
                }
                type="checkbox"
              />
              <span>Enable Stable Horde fallback images</span>
            </label>

            <label className="field field--checkbox">
              <input
                checked={jobForm.diagnostics_mode}
                onChange={(event) =>
                  setJobForm((current) => ({
                    ...current,
                    diagnostics_mode: event.target.checked,
                  }))
                }
                type="checkbox"
              />
              <span>Render with diagnostics overlays</span>
            </label>
          </div>

          {createJob.isError ? (
            <p className="error-copy">{(createJob.error as Error).message}</p>
          ) : null}

          <div className="form-actions">
            <button className="button" disabled={createJob.isPending} type="submit">
              {createJob.isPending ? "Queueing..." : "Create job"}
            </button>
            <Link className="button button--ghost" to="/">
              Back to dashboard
            </Link>
          </div>
        </form>
      </div>
    </section>
  );
}
