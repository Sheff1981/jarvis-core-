"""Read-only context assembly for a project's next dialogue turn."""
from jarvis.dialogue_memory import DialogueMemory
from jarvis.projects import Projects


def build_project_context(project_id, db_path="jarvis.db", limit=20):
    """Return bounded, project-scoped context without executing actions."""
    projects = Projects(db_path)
    try:
        project = next((item for item in projects.list(include_done=True)
                        if item["id"] == project_id), None)
    finally:
        projects.close()
    if project is None:
        raise KeyError("Project not found")
    dialogue = DialogueMemory(db_path)
    try:
        history = dialogue.recent(project_id, limit=limit)
    finally:
        dialogue.close()
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "status": project["status"],
        "next_step": project["next_step"],
        "messages": [{"role": item["role"], "content": item["content"]}
                     for item in history],
    }
