import { Link } from "react-router-dom";

import type { Project } from "../types/api";
import { StatusBadge } from "./StatusBadge";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link to={`/projects/${project.id}`} className="project-card">
      <div className="project-card__topline">
        <StatusBadge label={project.status} />
        <span>{project.requested_duration_minutes} min</span>
      </div>
      <h3>{project.title}</h3>
      <p>{project.prompt}</p>
      <div className="project-card__meta">
        <span>{project.visual_style.replace(/_/g, " ")}</span>
        <span>{project.topic_domain ?? "general explainer"}</span>
      </div>
    </Link>
  );
}
