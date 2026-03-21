
from collections import Counter, defaultdict

import pandas as pd

LEVELS = ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"]

def detect_type_columns(df):
    col_map = {}
    for i, col in enumerate(df.columns):
        col_lower = str(col).lower()
        if "điền từ" in col_lower:
            col_map["Điền từ"] = i
        elif "sắp xếp" in col_lower:
            col_map["Sắp xếp"] = i
        elif "đọc hiểu" in col_lower:
            col_map["Đọc hiểu"] = i
        elif "điền cụm" in col_lower:
            col_map["Điền cụm từ/điền câu"] = i
    return col_map


def detect_all_levels(row, start_index):
    found = []
    for offset in range(4):
        cell = row.iloc[start_index + offset]
        if pd.notna(cell) and str(cell).strip() != "":
            found.append(LEVELS[offset])
    return found


META_COLS = ["STT", "Chủ đề", "Số từ","Từ vựng", "Độ khó", "Dạng thức bài đọc (VI)","Dạng thức bài đọc (EN)","Từ vựng tham khảo","Tài liệu tham khảo"]


def extract_blocks_from_excel(file_path: str):

    df = pd.read_excel(file_path, sheet_name="Ma trận")
    df.columns = [str(col).strip() for col in df.columns]
    df[META_COLS] = df[META_COLS].ffill()

    type_col_map = detect_type_columns(df)
    blocks = []
    total_counts = Counter()
    grouped = df.groupby("STT")

    for stt, group in grouped:
        topic = group.iloc[0]["Chủ đề"]
        vocabulary_example = group.iloc[0]["Từ vựng"]
        word_count = str(group.iloc[0]["Số từ"])
        difficulty = group.iloc[0]["Độ khó"]
        text_type = group.iloc[0]["Dạng thức bài đọc (VI)"]
        text_type_en = group.iloc[0]["Dạng thức bài đọc (EN)"]
        vocabulary = group.iloc[0]["Từ vựng tham khảo"]
        document_sample = group.iloc[0]["Tài liệu tham khảo"]
        question_types = defaultdict(list)

        for _, row in group.iterrows():
            spec = row.get("Đặc tả ma trận")
            if pd.isna(spec):
                continue
            spec = str(spec).strip()
            for q_type, start_col in type_col_map.items():
                levels = detect_all_levels(row, start_col)
                for lv in levels:
                    question_types[q_type].append({"spec": spec, "level": lv})

        print(f"\n=== STT {stt} ===")
        for q_type, questions in question_types.items():
            count = len(questions)
            print(f"{q_type}: {count} questions")
            total_counts[q_type] += count
            blocks.append({
                "type": q_type,
                "topic": topic,
                "difficulty": difficulty,
                "text_type": text_type,
                "text_type_en": text_type_en,
                "word_count": word_count,
                "question_count": count,
                "questions": questions,
                "vocabulary": vocabulary,
                "document_sample": document_sample,
                "vocabulary_example": vocabulary_example

            })

    print("\n=== TOTAL QUESTIONS PER COLUMN ===")
    for q_type, count in total_counts.items():
        print(f"{q_type}: {count}")

    return blocks
