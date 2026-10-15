"""Conservative autonomous learning tick: network checks, budgets and goals.

This planner does not execute code, install packages, or visit arbitrary sites.
It only dispatches approved Academy documentation research when online.
"""
import socket
import time
from jarvis.learning_director import LearningDirector
from jarvis.academy import Academy, SOURCES
from jarvis.research_agent import ResearchAgent


CURRICULUM = {
    "programming": ("python", "https://docs.python.org/3/"),
    "engineering": ("web", "https://developer.mozilla.org/en-US/docs/Web"),
    "cybersecurity": ("security", "https://cheatsheetseries.owasp.org/"),
}


def internet_available(*, probe=None):
    if probe is not None:
        return bool(probe())
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=2):
            return True
    except OSError:
        return False


class AutonomousLearningLoop:
    def __init__(self, db_path="jarvis.db", *, online_probe=None, researcher_factory=None):
        self.db_path = db_path
        self.online_probe = online_probe
        self.researcher_factory = researcher_factory

    def tick(self, *, enabled=False, max_pages=2):
        if not enabled:
            return {"status": "disabled", "pages": 0}
        if not isinstance(max_pages, int) or not 1 <= max_pages <= 5:
            raise ValueError("Invalid research budget")
        if not internet_available(probe=self.online_probe):
            return {"status": "offline", "pages": 0}
        director = LearningDirector(self.db_path)
        academy = Academy(self.db_path)
        try:
            goals = director.next_goals(limit=max_pages)
            if not goals:
                return {"status": "no_goals", "pages": 0}
            agent = (self.researcher_factory(academy) if self.researcher_factory
                     else ResearchAgent(academy))
            attempted = 0
            outcomes = []
            for goal in goals:
                mapping = CURRICULUM.get(goal["domain"])
                if not mapping:
                    outcomes.append({"goal": goal["id"], "status": "no_approved_source"})
                    continue
                skill, url = mapping
                attempted += 1
                try:
                    result = agent.study(url, skill)
                    outcomes.append({"goal": goal["id"], "status": result.status,
                                     "url": result.url})
                    # Unreviewed web pages must never count as learned sessions.
                except (ValueError, RuntimeError, OSError) as exc:
                    outcomes.append({"goal": goal["id"], "status": "error",
                                     "reason": type(exc).__name__})
            return {"status": "research_attempted", "pages": attempted, "results": outcomes}
        finally:
            academy.close()
            director.close()
