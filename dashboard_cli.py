"""Run the local-only JARVIS dashboard."""
import argparse
from jarvis.dashboard import serve


def main(argv=None):
    parser = argparse.ArgumentParser(description="JARVIS local dashboard")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    print("JARVIS dashboard: http://127.0.0.1:%d" % args.port)
    try:
        serve(port=args.port, db_path=args.db)
    except KeyboardInterrupt:
        print("Dashboard stopped")


if __name__ == "__main__":
    main()
