import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../hooks/useAuth";

export function JobPage() {
  const { jobId } = useParams();
  const { isAuthenticated, signInWithGoogle } = useAuth();

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: Boolean(jobId && isAuthenticated),
    refetchInterval(query) {
      const status = query.state.data?.job.status;
      return status === "completed" || status === "failed" || status === "canceled" ? false : 5000;
    },
  });

  const logsQuery = useQuery({
    queryKey: ["job-logs", jobId],
    queryFn: () => api.getJobLogs(jobId!),
    enabled: Boolean(jobId && isAuthenticated),
    refetchInterval: 7000,
  });

  const retryMutation = useMutation({
    mutationFn: () => api.retryJob(jobId!),
    onSuccess: () => {
      void jobQuery.refetch();
      void logsQuery.refetch();
    },
  });

  const rerenderMutation = useMutation({
    mutationFn: (sceneId: string) => api.rerenderScene(jobId!, sceneId),
    onSuccess: () => {
      void jobQuery.refetch();
      void logsQuery.refetch();
    },
  });

  if (!isAuthenticated) {
    return (
      <section className="panel panel--empty">
        <h1>Sign in to inspect this job</h1>
        <button className="button" onClick={() => void signInWithGoogle()} type="button">
          Sign in with Google
        </button>
      </section>
    );
  }

  if (jobQuery.isLoading) {
    return <section className="panel">Loading job...</section>;
  }

  if (!jobQuery.data) {
    return <section className="panel panel--empty">Job not found.</section>;
  }

  const { job, scenes, video_spec: videoSpec } = jobQuery.data;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Render job</span>
          <h1>{videoSpec?.title ?? `Job ${job.id}`}</h1>
        </div>
        <StatusBadge label={job.status} />
      </div>

      <div className="detail-grid">
        <article className="panel">
          <div className="metric-row">
            <div>
              <span className="metric-row__label">Progress</span>
              <strong>{job.progress_pct}%</strong>
            </div>
            <div>
              <span className="metric-row__label">Provider</span>
              <strong>{job.llm_provider}</strong>
            </div>
            <div>
              <span className="metric-row__label">Resolution</span>
              <strong>{job.target_resolution}</strong>
            </div>
          </div>
          <ProgressBar value={job.progress_pct} />
          <p className="muted">
            Current step: {job.current_step ?? "queued"} - Retry count: {job.retry_count}
          </p>
          {job.error_message ? <p className="error-copy">{job.error_message}</p> : null}
          <div className="form-actions">
            {job.status === "completed" ? (
              <button className="button" onClick={() => void api.downloadExport(job.id)} type="button">
                Download export
              </button>
            ) : null}
            {job.status === "failed" ? (
              <button className="button" onClick={() => retryMutation.mutate()} type="button">
                {retryMutation.isPending ? "Retrying..." : "Retry failed scenes"}
              </button>
            ) : null}
            <Link className="button button--ghost" to={`/projects/${job.project_id}`}>
              Back to project
            </Link>
          </div>
        </article>

        <article className="panel">
          <h2>Outline preview</h2>
          {videoSpec ? (
            <>
              <p className="long-copy">{videoSpec.objective}</p>
              <div className="tag-row">
                <span>{videoSpec.scene_count} scenes</span>
                <span>{Math.round(videoSpec.target_duration_seconds / 60)} min target</span>
                <span>{videoSpec.style.replace(/_/g, " ")}</span>
              </div>
            </>
          ) : (
            <p className="muted">The planner output is not available for this job.</p>
          )}
        </article>
      </div>

      <section className="panel">
        <div className="section-heading section-heading--compact">
          <h2>Scenes</h2>
          <span className="muted">{scenes.length} scene specs</span>
        </div>
        <div className="scene-list">
          {scenes.map((scene) => (
            <article className="scene-card" key={scene.id}>
              <div className="scene-card__header">
                <div>
                  <span className="scene-card__index">Scene {scene.order_index}</span>
                  <h3>{scene.title}</h3>
                </div>
                <StatusBadge label={scene.status} />
              </div>
              <p>{scene.learning_objective}</p>
              <p className="muted">
                {Math.round(scene.estimated_duration_seconds)} sec - {scene.renderer_key} renderer
              </p>
              {scene.last_error ? <p className="error-copy">{scene.last_error}</p> : null}
              <div className="form-actions">
                <button
                  className="button button--ghost"
                  onClick={() => rerenderMutation.mutate(scene.id)}
                  type="button"
                >
                  {rerenderMutation.isPending ? "Queueing..." : "Rerender scene"}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="section-heading section-heading--compact">
          <h2>Logs</h2>
          <span className="muted">{logsQuery.data?.length ?? 0} events</span>
        </div>
        <div className="log-list">
          {logsQuery.data?.map((log) => (
            <article className="log-entry" key={log.id}>
              <div className="log-entry__topline">
                <StatusBadge label={log.level.toLowerCase()} />
                <span>{new Date(log.created_at).toLocaleString()}</span>
              </div>
              <strong>{log.event}</strong>
              <p>{log.message}</p>
            </article>
          )) ?? <p className="muted">No logs yet.</p>}
        </div>
      </section>
    </section>
  );
}
