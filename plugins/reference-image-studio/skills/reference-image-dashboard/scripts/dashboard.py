#!/usr/bin/env python3
"""Build an offline reference-image project dashboard (Python 3.9+, stdlib)."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from urllib.parse import quote

IMAGE_TYPES = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
ASSETS = Path(__file__).resolve().parent.parent / 'assets'


def local(root, value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Expected a nonempty project-relative POSIX path')
    p = Path(value)
    if p.is_absolute() or '..' in p.parts or ':' in p.parts[0]:
        raise ValueError('Path must stay inside project: ' + value)
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Symlink escapes project: ' + value)
    return target


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        f.write(content.encode('utf-8'))
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, data):
    atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def init(root, title=None):
    root.mkdir(parents=True, exist_ok=True)
    for folder in ['references', 'inputs', 'tasks', 'retained', '.studio', 'dashboard']:
        local(root, folder).mkdir(exist_ok=True)
    path = local(root, '.studio/project.json')
    if not path.exists():
        dump(path, {'schema_version': 1, 'title': title or root.name,
                    'references': [], 'tasks': [], 'retained': [],
                    'scan_roots': ['references', 'inputs', 'tasks', 'retained']})
    return build(root)


def require(obj, fields, context):
    if not isinstance(obj, dict):
        raise ValueError(context + ': expected object')
    for key in fields:
        if not isinstance(obj.get(key), str) or not obj[key].strip():
            raise ValueError(context + ': missing string ' + key)


def unique(items, context):
    if not isinstance(items, list):
        raise ValueError(context + ': expected array')
    ids = []
    for item in items:
        require(item, ['id'], context)
        ids.append(item['id'])
    if len(ids) != len(set(ids)):
        raise ValueError(context + ': duplicate id')


def validate(project, tasks):
    if project.get('schema_version') != 1:
        raise ValueError('Unsupported project schema_version')
    require(project, ['title'], 'project')
    archive_paths = []
    for entry in project.get('archives', []):
        require(entry, ['path', 'reason'], 'archive')
        if not isinstance(entry.get('archived'), bool):
            raise ValueError('archive.archived must be boolean')
        archive_paths.append(entry['path'])
    if len(archive_paths) != len(set(archive_paths)):
        raise ValueError('Duplicate archive path')
    unique(tasks, 'tasks')
    outputs = {}
    for task in tasks:
        require(task, ['id', 'title', 'kind', 'status'], 'task')
        if task['status'] not in {'planned', 'running', 'completed', 'failed', 'cancelled', 'unknown'}:
            raise ValueError('Unknown task status: ' + task['status'])
        unique(task.get('steps', []), 'steps')
        for step in task.get('steps', []):
            require(step, ['id', 'version', 'status'], 'step')
            if step['status'] not in {'planned', 'running', 'completed', 'failed', 'cancelled', 'unknown'}:
                raise ValueError('Unknown step status')
            unique(step.get('outputs', []), 'outputs')
            for item in step.get('inputs', []):
                require(item, ['path', 'role'], 'input')
                if item.get('sent') is not None and not isinstance(item['sent'], bool):
                    raise ValueError('input.sent must be true, false or null')
            for item in step.get('outputs', []):
                require(item, ['id', 'path'], 'output')
                outputs[(task['id'], step['id'], item['id'])] = item
    for kind in ['references', 'retained']:
        unique(project.get(kind, []), kind)
        for item in project.get(kind, []):
            require(item, ['id', 'title', 'path', 'scope', 'status'], kind)
            if kind == 'references':
                require(item, ['source'], kind)
            allowed = {'confirmed', 'provisional', 'superseded'} if kind == 'references' else {'retained', 'superseded'}
            if item['status'] not in allowed:
                raise ValueError('Unknown ' + kind + ' status')
            if item['status'] in {'confirmed', 'retained'}:
                require(item, ['confirmation'], kind)
            origin = item.get('origin')
            if kind == 'retained' and not origin:
                raise ValueError('Retained result needs task/step/output origin')
            if origin:
                require(origin, ['task', 'step', 'output'], 'origin')
                if tuple(origin[k] for k in ['task', 'step', 'output']) not in outputs:
                    raise ValueError('Unknown origin: ' + str(origin))
    return outputs


def dimensions(path):
    """Best effort PNG/JPEG/GIF size without an image dependency."""
    try:
        with path.open('rb') as f:
            head = f.read(24)
            if head.startswith(b'\x89PNG\r\n\x1a\n'):
                return list(struct.unpack('>II', head[16:24]))
            if head[:6] in [b'GIF87a', b'GIF89a']:
                return list(struct.unpack('<HH', head[6:10]))
            if head[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    byte = f.read(1)
                    if not byte:
                        break
                    if byte != b'\xff':
                        continue
                    marker = f.read(1)
                    while marker == b'\xff':
                        marker = f.read(1)
                    if marker in [b'\xd9', b'\xda', b'']:
                        break
                    if marker in [b'\xd8', b'\x01'] or 0xd0 <= marker[0] <= 0xd7:
                        continue
                    length = struct.unpack('>H', f.read(2))[0]
                    if marker[0] in [0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]:
                        _, h, w = struct.unpack('>BHH', f.read(5))
                        return [w, h]
                    f.seek(length - 2, 1)
    except (OSError, ValueError, struct.error, IndexError):
        pass
    return None


def validate_paths(root, value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'path':
                local(root, item)
            else:
                validate_paths(root, item)
    elif isinstance(value, list):
        for item in value:
            validate_paths(root, item)


def validate_copies(root, project, tasks):
    output_map = validate(project, tasks)
    for item in project.get('retained', []):
        origin = item['origin']
        source = output_map[tuple(origin[k] for k in ['task', 'step', 'output'])]
        target_path, source_path = local(root, item['path']), local(root, source['path'])
        if target_path.is_file() and source_path.is_file() and target_path.read_bytes() != source_path.read_bytes():
            raise ValueError('Retained copy differs from its origin; register a new output: ' + item['id'])


def read_project(root):
    project = load(local(root, '.studio/project.json'))
    paths = list(project.get('tasks', []))
    # Only task manifests are auto-discovered; arbitrary filenames never imply approval.
    paths += [str(p.relative_to(root)) for p in (root / 'tasks').glob('*/task.json')]
    tasks = []
    for name in dict.fromkeys(paths):
        task = load(local(root, name))
        task['_record'] = name
        tasks.append(task)
    validate(project, tasks)
    validate_paths(root, project)
    validate_paths(root, tasks)
    for folder in project.get('scan_roots', []):
        local(root, folder)
    validate_copies(root, project, tasks)
    return project, tasks


def build(root):
    root = root.expanduser().resolve()
    project, tasks = read_project(root)
    warnings, known, cache = [], set(), {}
    archives = {str(local(root, x['path']).relative_to(root)): x for x in project.get('archives', [])}
    thumb_dir = local(root, 'dashboard/thumbnails')
    thumb_dir.mkdir(parents=True, exist_ok=True)

    def asset(name):
        path = local(root, name)
        known.add(name)
        if name in cache:
            return cache[name]
        url = '../' + quote(name, safe='/')
        result = {'path': name, 'url': url, 'exists': path.is_file(),
                  'archived': archives.get(str(path.relative_to(root)), {}).get('archived', False)}
        if not path.is_file():
            warnings.append('Missing file: ' + name)
        else:
            result['bytes'] = path.stat().st_size
            if path.suffix.lower() in IMAGE_TYPES:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                result.update(sha256=digest, dimensions=dimensions(path), image=True)
                thumb = local(root, 'dashboard/thumbnails/' + digest + '.jpg')
                if not thumb.exists():
                    # sips is optional; every platform can still render original local files.
                    if shutil.which('sips'):
                        try:
                            subprocess.run(['sips', '-s', 'format', 'jpeg', '-Z', '640', str(path), '--out', str(thumb)],
                                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
                        except (OSError, subprocess.SubprocessError):
                            thumb.unlink(missing_ok=True)
                result['thumb'] = 'thumbnails/' + digest + '.jpg' if thumb.exists() else url
        cache[name] = result
        return result

    def text_doc(doc):
        if not isinstance(doc, dict):
            raise ValueError('prompt/document must be an object')
        if doc.get('path'):
            path = local(root, doc['path'])
            a = asset(doc['path'])
            return {**doc, 'asset': a, 'text': path.read_text(encoding='utf-8') if path.is_file() else '[文件缺失]'}
        return {**doc, 'text': doc.get('text', '[未记录]')}

    refs = copy.deepcopy(project.get('references', []))
    kept = copy.deepcopy(project.get('retained', []))
    for item in refs + kept:
        item['asset'] = asset(item['path'])
        item['documents'] = [text_doc(d) for d in item.get('documents', [])]
    for task in tasks:
        task['documents'] = [text_doc(d) for d in task.get('documents', [])]
        for step in task.get('steps', []):
            step['prompt'] = text_doc(step.get('prompt', {}))
            for item in step.get('inputs', []) + step.get('outputs', []):
                item['asset'] = asset(item['path'])
    unregistered = []
    for folder in project.get('scan_roots', []):
        directory = local(root, folder)
        if directory.is_dir():
            for path in sorted(directory.rglob('*')):
                if path.is_file() and path.suffix.lower() in IMAGE_TYPES:
                    name = str(path.relative_to(root))
                    if name not in known and 'dashboard' not in Path(name).parts:
                        unregistered.append({'id': 'unregistered:' + name, 'title': path.name,
                                             'path': name, 'asset': asset(name)})
    archived_items = [{**item, 'asset': asset(item['path'])} for item in archives.values() if item.get('archived')]
    payload = {'archives': archived_items, 'title': project['title'], 'references': refs, 'tasks': tasks,
               'retained': kept, 'unregistered': unregistered, 'warnings': warnings}
    encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ASSETS / 'index.html').read_text(encoding='utf-8')
    atomic(local(root, 'dashboard/index.html'), template.replace('/*__PROJECT_DATA__*/', encoded))
    print('Dashboard: ' + str(root / 'dashboard/index.html'))
    print(f"{len(refs)} references, {len(tasks)} tasks, {len(kept)} retained, {len(unregistered)} unregistered")
    for warning in warnings:
        print('Warning: ' + warning)
    return payload


def record(root, kind, filename):
    root = root.expanduser().resolve()
    project, _ = read_project(root)
    path = local(root, filename)
    item = load(path)
    if kind == 'task':
        if filename not in project['tasks']:
            project['tasks'].append(filename)
    else:
        require(item, ['id'], kind)
        key = {'reference': 'references', 'retained': 'retained'}[kind]
        items = project[key]
        existing = next((i for i, r in enumerate(items) if r['id'] == item['id']), None)
        if existing is None:
            items.append(item)
        else:
            items[existing] = item
    # Validate candidate before replacing the registry or generated page.
    task_paths = list(dict.fromkeys(project['tasks'] + [str(p.relative_to(root)) for p in (root / 'tasks').glob('*/task.json')]))
    validate(project, [load(local(root, p)) for p in task_paths])
    validate_paths(root, item)
    validate_copies(root, project, [load(local(root, p)) for p in task_paths])
    dump(local(root, '.studio/project.json'), project)
    build(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'build', 'check', 'record'])
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--title')
    parser.add_argument('--kind', choices=['reference', 'task', 'retained'])
    parser.add_argument('--file', help='JSON record path relative to workspace')
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    try:
        if args.command == 'init': init(root, args.title)
        elif args.command == 'record':
            if not args.kind or not args.file: parser.error('record needs --kind and --file')
            record(root, args.kind, args.file)
        elif args.command == 'check':
            read_project(root)
            print('Project records valid')
        else: build(root)
    except (ValueError, OSError, KeyError, TypeError) as e:
        parser.exit(1, 'Error: ' + str(e) + '\n')


if __name__ == '__main__':
    main()
