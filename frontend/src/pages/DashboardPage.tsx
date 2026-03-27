import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { ProjectCard } from "../components/ProjectCard";
import { useAuth } from "../hooks/useAuth";

const demoPrompts = [
  "Explain gradient descent visually with equations, contour plots, and intuition.",
  "Teach Laplace transforms from first principles with derivations and engineering examples.",
  "Build a 12 minute explainer on binary search trees, balancing, and runtime tradeoffs.",
];

export function DashboardPage() {
  const { isAuthenticated, isLoading, signInWithGoogle } = useAuth();
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
    enabled: isAuthenticated,
  });

  if (!isLoading && !isAuthenticated) {
    return (
      <section className="hero-panel">
        <div className="hero-panel__content">
          <span className="eyebrow">Long-form explainer video generation</span>
          <h1>Plan, inspect, and render technical videos scene by scene.</h1>
          <p>
            MindWise turns prompts into modular explainers with structured scene plans,
            resumable jobs, and per-scene review.
          </p>
          <div className="hero-panel__actions">
            <button className="button" onClick={() => void signInWithGoogle()} type="button">
              Sign in with Google
            </button>
            <Link className="button button--ghost" to="/projects/new">
              Explore the workflow
            </Link>
          </div>
        </div>

        <div className="hero-panel__rail">
          <h2>Demo prompts</h2>
          <ul className="demo-list">
            {demoPrompts.map((prompt) => (
              <li key={prompt}>{prompt}</li>
            ))}
          </ul>
        </div>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Workspace</span>
          <h1>Your video projects</h1>
        </div>
        <Link className="button" to="/projects/new">
          Create project
        </Link>
      </div>

      <div className="stats-strip">
        <article>
          <strong>{projectsQuery.data?.length ?? 0}</strong>
          <span>Projects</span>
        </article>
        <article>
          <strong>1-30 min</strong>
          <span>Target duration range</span>
        </article>
        <article>
          <strong>Scene-by-scene</strong>
          <span>Retry and diagnostics workflow</span>
        </article>
      </div>

      {projectsQuery.isLoading ? (
        <div className="panel">Loading projects...</div>
      ) : projectsQuery.data?.length ? (
        <div className="project-grid">
          {projectsQuery.data.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="panel panel--empty">
          <h2>No projects yet</h2>
          <p>Start with a topic, duration, and visual style. The backend will generate the lesson plan and queue the render job.</p>
          <Link className="button" to="/projects/new">
            Create your first project
          </Link>
        </div>
      )}
    </section>
  );
}
