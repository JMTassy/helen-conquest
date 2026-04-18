#!/usr/bin/env python3
"""
Auto-generate CLAUDE.md documentation indices.

This script creates:
1. scratchpad/CLAUDE_MD_LINE_INDEX.txt — Line ranges by heading
2. scratchpad/CLAUDE_MD_SECTIONS_BY_LENGTH.txt — Sections ordered by size

Run from repo root:
    python3 scratchpad/generate_claude_index.py

Features:
- GitHub-like anchor slug generation (best-effort)
- Handles duplicate heading names with numeric suffixes (-1, -2, etc.)
- Correctly skips headings inside fenced code blocks (``` and ~~~)
- Accurate section length calculation (extends to actual file length)
"""

from pathlib import Path
import re
from collections import defaultdict


def generate_github_slug(text):
    """
    Generate GitHub-like anchor slugs (best-effort).

    Rules:
    - Lowercase
    - Remove special characters (keep hyphens and spaces)
    - Convert spaces to hyphens
    - Collapse multiple hyphens

    Note: GitHub's actual algorithm has edge cases with unicode and emojis.
    This implementation handles common ASCII headings correctly.
    """
    # Lowercase
    slug = text.lower()

    # Replace non-alphanumeric (except spaces/hyphens) with empty
    # Keep alphanumerics, spaces, and hyphens
    slug = re.sub(r'[^a-z0-9\s\-]', '', slug)

    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)

    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def extract_headings(src_path):
    """
    Extract markdown headings, correctly skipping code blocks.

    Handles:
    - ``` fenced blocks
    - ~~~ fenced blocks
    - Tracks fence type to prevent false closes

    Note: Anchor slug generation is GitHub-like (best-effort).
    GitHub's anchor algorithm has edge cases with unicode, emojis, etc.
    This implementation handles common cases correctly.
    """
    text = src_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_code = False
    code_fence = None  # Track which fence opened the block
    headings = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Check for code fence markers
        code_fence_match = re.match(r'^(```|~~~)', stripped)
        if code_fence_match:
            fence_type = code_fence_match.group(1)

            if not in_code:
                # Opening fence
                in_code = True
                code_fence = fence_type
            elif code_fence == fence_type:
                # Closing fence (matching type)
                in_code = False
                code_fence = None
            # else: different fence type inside block, ignore
            continue

        # Only process headings outside code blocks
        if not in_code:
            match = re.match(r"^(#+)\s+(.+?)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((i, level, title))

    return headings, len(lines)


def generate_anchor_map(headings):
    """
    Generate GitHub-like anchors, handling duplicates (best-effort).

    Returns:
    - anchor_map: dict {heading_index: anchor_slug}
    - slug_occurrence: dict {heading_index: (base_slug, occurrence_number)}
    - duplicates_report: list of tuples (base_slug, total_count, anchor_list)

    For duplicate slugs, appends -1, -2, etc. (following GitHub convention).
    First occurrence has no suffix, second gets -1, third gets -2, etc.
    """
    slug_counts = defaultdict(int)
    slug_occurrence_map = {}  # Maps idx to (base_slug, occurrence_number)
    slug_to_indices = defaultdict(list)  # Maps base_slug to list of (idx, anchor)
    anchor_map = {}

    for idx, (_, _, title) in enumerate(headings):
        base_slug = generate_github_slug(title)

        # Count occurrences of this slug
        slug_counts[base_slug] += 1
        count = slug_counts[base_slug]

        # GitHub convention: first occurrence has no suffix, second gets -1, third gets -2
        if count == 1:
            anchor = base_slug
        else:
            anchor = f"{base_slug}-{count - 1}"

        anchor_map[idx] = anchor
        slug_occurrence_map[idx] = (base_slug, count)
        slug_to_indices[base_slug].append((idx, anchor))

    # Build duplicates report (only slugs with count > 1)
    duplicates_report = []
    for base_slug in sorted(slug_counts.keys()):
        if slug_counts[base_slug] > 1:
            anchors = [anchor for _, anchor in slug_to_indices[base_slug]]
            duplicates_report.append((base_slug, slug_counts[base_slug], anchors))

    return anchor_map, slug_occurrence_map, duplicates_report


def generate_line_index(headings, anchor_map, slug_occurrence_map, duplicates_report, total_lines):
    """Generate line range index by heading with base slug and occurrence info."""
    lines = [
        "CLAUDE.md — AUTO-GENERATED LINE INDEX",
        "=" * 80,
        "",
    ]

    for idx, (lineno, level, title) in enumerate(headings):
        next_line = headings[idx + 1][0] if idx + 1 < len(headings) else total_lines + 1
        end_line = next_line - 1
        indent = "  " * (level - 1)
        marker = "#" * level
        anchor = anchor_map[idx]
        base_slug, occurrence = slug_occurrence_map[idx]

        lines.append(f"{indent}- {marker} {title}")

        # For duplicates, show base slug and occurrence number explicitly
        if occurrence > 1:
            lines.append(f"{indent}  Lines {lineno}–{end_line} | Base: #{base_slug} | Occurrence: {occurrence} | Anchor: #{anchor}")
        else:
            lines.append(f"{indent}  Lines {lineno}–{end_line} | Anchor: #{anchor}")
        lines.append("")

    # Add duplicates report section
    if duplicates_report:
        lines.append("=" * 80)
        lines.append("")
        lines.append("DUPLICATE HEADINGS (Deterministic Verification)")
        lines.append("")
        for base_slug, count, anchors in duplicates_report:
            lines.append(f"• {base_slug} (appears {count} times)")
            for i, anchor in enumerate(anchors, start=1):
                occurrence_label = f"occurrence {i}" if i > 1 else "first occurrence"
                lines.append(f"  - {occurrence_label}: #{anchor}")
            lines.append("")

    lines.append("=" * 80)
    lines.append("")
    lines.append("Generated by: scratchpad/generate_claude_index.py")
    lines.append("(Do not edit manually)")

    return "\n".join(lines)


def generate_section_length_index(headings, total_lines):
    """
    Generate section sizes (H2 headings only).

    Correctly handles final section extending to end of file.
    """
    # Extract H2 sections with their line ranges
    h2_sections = []

    for idx, (lineno, level, title) in enumerate(headings):
        if level == 2:
            # Find end: either next H2 heading, or end of file
            end_line = total_lines
            for jdx in range(idx + 1, len(headings)):
                if headings[jdx][1] == 2:  # Next H2
                    end_line = headings[jdx][0] - 1
                    break

            size = end_line - lineno + 1
            h2_sections.append((title, size, lineno, end_line))

    # Sort by size descending
    h2_sections.sort(key=lambda x: x[1], reverse=True)

    lines = [
        "CLAUDE.md — SECTIONS BY LENGTH (Auto-Generated)",
        "=" * 80,
        "",
    ]

    for title, size, start, end in h2_sections:
        lines.append(f"• {title}: {size} lines (Lines {start}–{end})")

    lines.append("")
    lines.append("=" * 80)
    lines.append("Generated by: scratchpad/generate_claude_index.py")
    lines.append("(Do not edit manually)")

    return "\n".join(lines)


def main():
    # Repo root is parent of scratchpad
    repo_root = Path(__file__).parent.parent
    claude_md = repo_root / "CLAUDE.md"

    if not claude_md.exists():
        print(f"ERROR: {claude_md} not found")
        return 1

    print(f"Reading: {claude_md}")
    headings, total_lines = extract_headings(claude_md)
    print(f"Found {len(headings)} headings, {total_lines} total lines")

    # Generate anchor map (returns 3 values now)
    anchor_map, slug_occurrence_map, duplicates_report = generate_anchor_map(headings)
    print(f"Generated anchors (with duplicate handling)")
    if duplicates_report:
        print(f"  - Found {len(duplicates_report)} base slugs with duplicates")

    # Generate line index
    line_index_path = repo_root / "scratchpad" / "CLAUDE_MD_LINE_INDEX.txt"
    line_index_content = generate_line_index(headings, anchor_map, slug_occurrence_map, duplicates_report, total_lines)
    line_index_path.parent.mkdir(parents=True, exist_ok=True)
    line_index_path.write_text(line_index_content, encoding="utf-8")
    print(f"✓ Generated: {line_index_path.name}")

    # Generate section length index
    length_index_path = repo_root / "scratchpad" / "CLAUDE_MD_SECTIONS_BY_LENGTH.txt"
    length_index_content = generate_section_length_index(headings, total_lines)
    length_index_path.write_text(length_index_content, encoding="utf-8")
    print(f"✓ Generated: {length_index_path.name}")

    print("\nAll indices generated successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
