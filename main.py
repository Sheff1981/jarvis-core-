import argparse
import platform
import time
from jarvis.core import Memory
from jarvis.windows import WindowsRecorder, replay


def main():
    parser = argparse.ArgumentParser(description='JARVIS MVP: Windows click recorder and replay')
    parser.add_argument('--db', default='jarvis.db')
    sub = parser.add_subparsers(dest='cmd', required=True)
    rec = sub.add_parser('record')
    rec.add_argument('name')
    sub.add_parser('list')
    play = sub.add_parser('replay')
    play.add_argument('id')
    play.add_argument('--execute', action='store_true', help='Actually click; default is preview')
    args = parser.parse_args()
    memory = Memory(args.db)
    if args.cmd == 'record':
        if platform.system() != 'Windows':
            parser.error('Recording requires Windows')
        recorder = WindowsRecorder()
        input('Press Enter to START recording mouse clicks...')
        recorder.start()
        input('Recording. Press Enter to STOP...')
        steps = recorder.stop()
        sid = memory.save(args.name, 'windows', steps)
        print(f'Saved {len(steps)} clicks: {sid}')
    elif args.cmd == 'list':
        for row in memory.list():
            print(*row, sep=' | ')
    else:
        scenario = memory.get(args.id)
        if scenario['platform'] != 'windows':
            parser.error('This runner only supports Windows scenarios')
        if args.execute and platform.system() != 'Windows':
            parser.error('Execution requires Windows')
        print('Scenario:', scenario['name'])
        if args.execute:
            print('Executing in 3 seconds. Move mouse to top-left corner to abort.')
            time.sleep(3)
        replay(scenario['steps'], dry_run=not args.execute)

if __name__ == '__main__':
    main()
