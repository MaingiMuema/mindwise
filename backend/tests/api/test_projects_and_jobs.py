from app.services.jobs.service import JobService


def test_project_and_job_creation_flow(client, auth_context, monkeypatch):
    headers, _ = auth_context
    monkeypatch.setattr(JobService, "enqueue", lambda self, job_id: None)

    project_response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "title": "Gradient Descent Explained",
            "prompt": "Explain gradient descent visually with equations, plots, and intuition.",
            "requested_duration_minutes": 6,
            "source_type": "prompt",
            "visual_style": "clean_academic",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    job_response = client.post(
        f"/api/v1/projects/{project_id}/jobs",
        headers=headers,
        json={"job_type": "preview", "requested_duration_minutes": 4, "image_generation_enabled": False},
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["job"]["project_id"] == project_id
    assert len(payload["scenes"]) >= 5
