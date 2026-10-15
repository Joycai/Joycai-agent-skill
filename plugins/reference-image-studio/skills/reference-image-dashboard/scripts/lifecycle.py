#!/usr/bin/env python3
"""Inspect dependencies, archive in place, or restore project image results."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import dashboard


def normalized(root, path):
    return str(dashboard.local(root, path).relative_to(root))


def inspect(root, paths):
    root = root.expanduser().resolve()
    project, tasks = dashboard.read_project(root)
    result = []
    for name in paths:
        name = normalized(root, name)
        target = dashboard.local(root, name)
        if target.suffix.lower() not in dashboard.IMAGE_TYPES or name.split('/')[0] in {'.studio', 'dashboard'}:
            raise ValueError('Only source/result images can be archived: ' + name)
        refs = []
        def visit(value, location):
            if isinstance(value, dict):
                if isinstance(value.get('path'), str) and normalized(root, value['path']) == name:
                    refs.append(location)
                for key, item in value.items():
                    if key != 'archives': visit(item, location + '/' + key)
            elif isinstance(value, list):
                for i, item in enumerate(value): visit(item, location + '/' + str(i))
        visit({k: v for k, v in project.items() if k != 'archives'}, 'project')
        for task in tasks: visit(task, 'task:' + task['id'])
        protected = [r for r in refs if r.startswith(('project/references/', 'project/retained/'))]
        # Textual mentions are advisory, not a complete semantic dependency graph.
        mentions = []
        roots = set(project.get('scan_roots', []) + ['references'])
        for folder in sorted(roots):
            directory = dashboard.local(root, folder)
            if not directory.is_dir(): continue
            for path in sorted(directory.rglob('*')):
                if path.suffix.lower() in {'.md', '.txt'} and path.is_file():
                    path = dashboard.local(root, str(path.relative_to(root)))
                    if name in path.read_text(encoding='utf-8', errors='replace'):
                        mentions.append(str(path.relative_to(root)))
        result.append({'path': name, 'exists': target.is_file(), 'references': refs,
                       'protected': protected, 'text_mentions': sorted(set(mentions))})
    return result


def update(root, paths, reason, restore=False, include_protected=False):
    root = root.expanduser().resolve()
    report = inspect(root, paths)
    if any(not item['exists'] for item in report):
        raise ValueError('Missing target file; no archive state changed')
    if not restore and not include_protected and any(item['protected'] for item in report):
        raise ValueError('Target is a reference or retained result; preserve by default. Explicit user scope is required for --include-protected')
    project, _ = dashboard.read_project(root)
    entries = project.setdefault('archives', [])
    now = datetime.now(timezone.utc).isoformat()
    for item in report:
        entry = next((x for x in entries if x['path'] == item['path']), None)
        if entry is None:
            if restore: raise ValueError('Target has no archive record: ' + item['path'])
            entry = {'path': item['path'], 'history': []}
            entries.append(entry)
        entry.update(archived=not restore, reason=reason)
        entry['history'].append({'action': 'restore' if restore else 'archive', 'at': now,
                                 'reason': reason, 'references': item['references'],
                                 'text_mentions': item['text_mentions']})
    # Only the registry changes. Image bytes, task manifests and historical links stay intact.
    registry = dashboard.local(root, '.studio/project.json')
    before = registry.read_text(encoding='utf-8')
    dashboard.dump(registry, project)
    try:
        dashboard.build(root)
    except Exception:
        dashboard.atomic(registry, before)
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'archive', 'restore'])
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--path', action='append', required=True, help='Exact project-relative image path; repeat for a batch')
    parser.add_argument('--reason', help='User request/reason, required for state changes')
    parser.add_argument('--include-protected', action='store_true', help='Only when user explicitly includes references/retained works')
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    try:
        if args.command == 'inspect': report = inspect(root, args.path)
        else:
            if not args.reason: parser.error('archive/restore requires --reason')
            report = update(root, args.path, args.reason, args.command == 'restore', args.include_protected)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, 'Error: ' + str(error) + '\n')


if __name__ == '__main__': main()
