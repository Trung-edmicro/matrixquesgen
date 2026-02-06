import pandas as pd
import sys
import os

# Set encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Đọc file Excel
file_path = r'E:\App\matrixquesgen\data\input\Ma trận_HOAHOC_KNTT_C11.xlsx'
df = pd.read_excel(file_path, sheet_name='Ma trận', header=None)

print('=' * 100)
print(f'PHÂN TÍCH CẤU TRÚC CÂU ĐÚNG/SAI (DS) - HOAHOC_KNTT_C11')
print('=' * 100)

# DS columns: 8, 9, 10 (NB, TH, VD)
DS_NB = 8
DS_TH = 9
DS_VD = 10

LESSON_COL = 3
SPEC_COL = 4

print('\n📋 Danh sách các câu DS trong ma trận:\n')

for row_idx in range(2, len(df)):  # Bỏ qua 2 hàng header
    row = df.iloc[row_idx]
    
    # Check nếu có câu DS
    has_ds = False
    ds_info = []
    
    if pd.notna(row[DS_NB]):
        has_ds = True
        ds_info.append(f"NB: {row[DS_NB]}")
    if pd.notna(row[DS_TH]):
        has_ds = True
        ds_info.append(f"TH: {row[DS_TH]}")
    if pd.notna(row[DS_VD]):
        has_ds = True
        ds_info.append(f"VD: {row[DS_VD]}")
    
    if has_ds:
        lesson = row[LESSON_COL] if pd.notna(row[LESSON_COL]) else "[Empty]"
        spec = row[SPEC_COL] if pd.notna(row[SPEC_COL]) else "[Empty]"
        
        print(f"Row {row_idx}:")
        print(f"  📖 Bài: {lesson}")
        print(f"  📝 Spec: {spec[:100]}...")
        print(f"  🎯 DS: {' | '.join(ds_info)}")
        print()

print('\n' + '=' * 100)
print('NHẬN XÉT:')
print('=' * 100)

# Phân tích các câu DS có nhiều hàng
print('\n🔍 Tìm các câu DS có statements nằm ở nhiều bài:\n')

# Track các statement codes
import re

all_statements = {}  # {code: [(row, lesson, level)]}

for row_idx in range(2, len(df)):
    row = df.iloc[row_idx]
    lesson = row[LESSON_COL] if pd.notna(row[LESSON_COL]) else None
    
    for col_idx, level in [(DS_NB, "NB"), (DS_TH, "TH"), (DS_VD, "VD")]:
        cell = row[col_idx]
        if pd.notna(cell):
            # Parse statements: "2 (C1a,C1b)" hoặc "2 (C2a,C2b)"
            match = re.search(r'\((.*?)\)', str(cell))
            if match:
                codes_str = match.group(1)
                codes = [c.strip().upper() for c in codes_str.split(',')]
                
                for code in codes:
                    if code not in all_statements:
                        all_statements[code] = []
                    all_statements[code].append((row_idx, lesson, level))

# Nhóm theo base question (C1a, C1b -> C1)
from collections import defaultdict
questions = defaultdict(list)

for stmt_code, locations in all_statements.items():
    # Extract base: C1A -> C1, C2B -> C2
    base_match = re.match(r'([Cc]\d+)', stmt_code)
    if base_match:
        base_code = base_match.group(1).upper()
        questions[base_code].append((stmt_code, locations))

# In ra các câu có statements ở nhiều bài khác nhau
for q_code in sorted(questions.keys()):
    statements = questions[q_code]
    
    # Check if statements come from different lessons
    all_lessons = set()
    for stmt_code, locations in statements:
        for row, lesson, level in locations:
            if lesson:
                all_lessons.add(lesson)
    
    if len(all_lessons) > 1:
        print(f"❗ Câu {q_code}: statements nằm ở {len(all_lessons)} bài khác nhau!")
        
        for stmt_code, locations in statements:
            for row, lesson, level in locations:
                print(f"   - {stmt_code} [{level}]: Row {row} - {lesson if lesson else '[Unknown]'}")
        print()

# Summary
print('\n📊 TỔNG KẾT:')
print(f"   • Tổng số câu DS: {len(questions)}")

multi_lesson_count = sum(1 for q_code in questions 
                         if len(set(lesson for _, locs in questions[q_code] 
                                   for _, lesson, _ in locs if lesson)) > 1)
print(f"   • Số câu có statements ở nhiều bài: {multi_lesson_count}")
print(f"   • Số câu trong cùng 1 bài: {len(questions) - multi_lesson_count}")
