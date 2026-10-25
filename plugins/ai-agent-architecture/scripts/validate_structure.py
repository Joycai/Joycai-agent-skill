#!/usr/bin/env python3
"""Check this plugin's entrypoints, references, migration inventory and manifests.

Local Markdown only; no network requests or API behavior assertions.
"""
from pathlib import Path
import json
import re
import sys
import unicodedata
from urllib.parse import unquote

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
EXPECTED = {
    'llm-api-integration', 'ai-media-api-integration',
    'agent-runtime-architecture', 'llm-provider-config', 'ai-usage-accounting',
}


def prose(text):
    """Ignore fenced examples and inline code when interpreting Markdown links."""
    text = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)
    return re.sub(r'`+[^`\n]*`+', '', text)


def slug(heading):
    heading = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', heading)
    heading = re.sub(r'<[^>]+>', '', heading).strip().lower()
    return ''.join(c for c in heading if c in '-_ ' or unicodedata.category(c)[0] in 'LN').replace(' ', '-')


def anchors(text):
    found = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        base = slug(heading)
        n = counts.get(base, 0)
        found.add(base if n == 0 else f'{base}-{n}')
        counts[base] = n + 1
    return found


def main():
    errors = []
    entries = list((BASE / 'skills').glob('*/SKILL.md'))
    actual = {p.parent.name for p in entries}
    if actual != EXPECTED:
        errors.append(f'Expected five skills; missing={EXPECTED-actual}, extra={actual-EXPECTED}')
    for p in entries:
        text = p.read_text()
        front = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        if not front:
            errors.append(f'{p}: missing frontmatter')
            continue
        if not re.search(r'^name: ' + re.escape(p.parent.name) + r'$', front[1], re.M):
            errors.append(f'{p}: name differs from directory')
        if not re.search(r'^description:\s*\S', front[1], re.M):
            errors.append(f'{p}: missing description')
    manifest = json.loads((BASE / '.claude-plugin/plugin.json').read_text())
    market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
    listing = next(p for p in market['plugins'] if p['name'] == manifest['name'])
    if listing['version'] != manifest['version'] or not re.fullmatch(r'\d+\.\d+\.\d+', manifest['version']):
        errors.append('Plugin and marketplace must declare the same semantic version')
    files = list(BASE.rglob('*.md')) + [ROOT / 'README.md']
    edges = {}
    links = 0
    for p in files:
        destinations = []
        for target in re.findall(r'(?<!!)\[[^]\n]+\]\(([^)\s]+)\)', prose(p.read_text())):
            if re.match(r'[a-zA-Z][\w+.-]*:', target):
                continue
            path, _, fragment = unquote(target).partition('#')
            dest = (p.parent / path).resolve() if path else p.resolve()
            links += 1
            if not dest.is_file():
                errors.append(f'{p.relative_to(ROOT)}: missing target {target}')
            elif fragment and dest.suffix == '.md' and fragment not in anchors(dest.read_text()):
                errors.append(f'{p.relative_to(ROOT)}: missing anchor {target}')
            destinations.append(dest)
        edges[p.resolve()] = destinations
    reached = set()
    pending = [p.resolve() for p in entries]
    while pending:
        p = pending.pop()
        if p not in reached:
            reached.add(p)
            pending.extend(edges.get(p, []))
    for p in (BASE / 'skills').glob('*/references/*.md'):
        if p.resolve() not in reached:
            errors.append(f'Unreachable reference: {p.relative_to(BASE)}')
    # Every pre-migration document must have a real documented target.
    inventory = (BASE / 'MIGRATION.md').read_text()
    moves = re.findall(r'^\| `skills/[^`]+` \| \[[^]]+\]\(([^)]+)\) \|$', inventory, re.M)
    if len(moves) != 40 or len(set(moves)) != 40:
        errors.append(f'Expected 40 unique migrated documents, found {len(moves)}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'PASS: {len(entries)} skills, {len(moves)} migration targets, {links} local links; all references reachable; version {manifest["version"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
