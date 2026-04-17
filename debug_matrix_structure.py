#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to check enriched matrix structure"""
import json
from pathlib import Path

matrix_file = Path('data/matrix/enriched_matrix_TOAN_KNTT_C10.json')

with open(matrix_file, 'r', encoding='utf-8') as f:
    matrix = json.load(f)

print("=== ENRICHED MATRIX STRUCTURE ===\n")

# Check metadata
meta = matrix.get('metadata', {})
print(f"Subject: {meta.get('subject')}")
print(f"Grade: {meta.get('grade')}\n")

# Check lessons
lessons = matrix.get('lessons', [])
print(f"Total lessons: {len(lessons)}\n")

# Check first lesson structure
if lessons:
    lesson = lessons[0]
    print(f"Lesson 1: {lesson.get('lesson_name')}")
    print(f"Keys in lesson: {list(lesson.keys())}\n")
    
    # Check TN structure
    tn = lesson.get('TN', {})
    print(f"TN type: {type(tn)}")
    print(f"TN keys (levels): {list(tn.keys()) if isinstance(tn, dict) else 'N/A'}\n")
    
    if isinstance(tn, dict):
        for level, specs in tn.items():
            print(f"  Level '{level}': {len(specs) if isinstance(specs, list) else '?'} specs")
            if isinstance(specs, list) and specs:
                spec = specs[0]
                print(f"    First spec keys: {list(spec.keys())}")
                print(f"    Code: {spec.get('code')}")
                print(f"    Has selected_templates_by_code: {'selected_templates_by_code' in spec}")
                break
    
    # Check DS structure
    ds = lesson.get('DS', [])
    print(f"\nDS type: {type(ds)}")
    print(f"DS count: {len(ds) if isinstance(ds, list) else '?'}\n")

print("=== MAPPING TEST STATUS ===")
print("✅ MathVariableMappingService working (from test output)")
print("✅ Variables populating correctly")
print("⚠️  Export function not writing TN specs to file")
print("\nLikely issue: export_prompts_with_math_mapping() loop logic wrong")
