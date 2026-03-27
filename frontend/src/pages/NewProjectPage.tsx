import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import type { ProjectCreatePayload, SourceType, VisualStyle } from "../types/api";

const styles: VisualStyle[] = [
  "clean_academic",
  "modern_infographic",
  "cinematic_technical",
  "playful_educational",
  "startup_explainer",
];

const sourceTypes: SourceType[] = ["prompt", "document", "lesson_request"];

export function NewProjectPage() {
  const navigate = useNavigate();
  const { isAuthenticated, signInWithGoogle } = useAuth();
  const [form, setForm] = useState<ProjectCreatePayload>({
    title: "",
    prompt: "",
    source_type: "prompt",
    requested_duration_minutes: 8,
    visual_style: "clean_academic",
    topic_domain: "",
    metadata_json: {},
  });

  const createProject = useMutation({
    mutationFn: api.createProject,
    onSuccess(project) {
      navigate(`/projects/${project.id}`);
    },
  });

  if (!isAuthenticated) {
    return (
      <section className="panel panel--empty">
        <h1>Sign in to create a project</h1>
        <p>The project form persists prompt, duration, and style, then lets you start a render job from the project detail page.</p>
        <button className="button" onClick={() => void signInWithGoogle()} type="button">
          Sign in with Google
        </button>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Project setup</span>
          <h1>Create a new explainer</h1>
        </div>
      </div>

      <form
        className="panel form-grid"
        onSubmit={(event) => {
          event.preventDefault();
          createProject.mutate({
            ...form,
            topic_domain: form.topic_domain || undefined,
          });
        }}
      >
        <label className="field field--span-2">
          <span>Title</span>
          <input
            required
            minLength={3}
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            placeholder="Explaining gradient descent visually"
          />
        </label>

        <label className="field field--span-2">
          <span>Prompt</span>
          <textarea
            required
            minLength={12}
            rows={8}
            value={form.prompt}
            onChange={(event) => setForm((current) => ({ ...current, prompt: event.target.value }))}
            placeholder="Describe the topic, desired depth, examples, equations, diagrams, and tone."
          />
        </label>

        <label className="field">
          <span>Source type</span>
          <select
            value={form.source_type}
            onChange={(event) =>
              setForm((current) => ({ ...current, source_type: event.target.value as SourceType }))
            }
          >
            {sourceTypes.map((sourceType) => (
              <option key={sourceType} value={sourceType}>
                {sourceType.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Target duration</span>
          <input
            type="number"
            min={1}
            max={30}
            value={form.requested_duration_minutes}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                requested_duration_minutes: Number(event.target.value),
              }))
            }
          />
        </label>

        <label className="field">
          <span>Visual style</span>
          <select
            value={form.visual_style}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                visual_style: event.target.value as VisualStyle,
              }))
            }
          >
            {styles.map((style) => (
              <option key={style} value={style}>
                {style.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Topic domain</span>
          <input
            value={form.topic_domain}
            onChange={(event) => setForm((current) => ({ ...current, topic_domain: event.target.value }))}
            placeholder="mathematics, ai_ml, finance..."
          />
        </label>

        <div className="form-actions field--span-2">
          {createProject.isError ? (
            <p className="error-copy">{(createProject.error as Error).message}</p>
          ) : null}
          <button className="button" disabled={createProject.isPending} type="submit">
            {createProject.isPending ? "Creating..." : "Create project"}
          </button>
        </div>
      </form>
    </section>
  );
}
