"""Minimal JARVIS project memory CLI. Works on Windows without dependencies."""
import argparse
from jarvis.projects import Projects

def main():
    parser = argparse.ArgumentParser(description="JARVIS project memory")
    parser.add_argument("--db", default="jarvis.db")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add a project")
    add.add_argument("name")
    add.add_argument("--next", default="", dest="next_step")
    show = commands.add_parser("list", help="Show unfinished projects")
    show.add_argument("--all", action="store_true")
    step = commands.add_parser("next", help="Set the next action")
    step.add_argument("id")
    step.add_argument("description")
    done = commands.add_parser("done", help="Mark a project finished")
    done.add_argument("id")
    args = parser.parse_args()
    db = Projects(args.db)
    try:
        if args.command == "add":
            print("Created:", db.add(args.name, args.next_step))
        elif args.command == "list":
            for item in db.list(include_done=args.all):
                print(f"{item['id']} | {item['status']} | {item['name']} | next: {item['next_step'] or 'not set'}")
        elif args.command == "next":
            db.update(args.id, next_step=args.description)
            print("Next action updated")
        elif args.command == "done":
            db.update(args.id, status="done")
            print("Project completed")
    finally:
        db.close()

if __name__ == "__main__":
    main()
