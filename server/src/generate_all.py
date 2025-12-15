"""
Main workflow: Sinh câu hỏi tự động cho cả TN (Trắc nghiệm) và DS (Đúng/Sai)
Output: File JSON chung chứa cả 2 dạng câu hỏi
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.genai_client import GenAIClient
from services.matrix_parser import MatrixParser
from services.question_generator import QuestionGenerator


def main():
    """Workflow chính sinh câu hỏi TN và DS"""
    
    print("\n" + "="*80)
    print("🚀 WORKFLOW: SINH CÂU HỎI TỰ ĐỘNG (TN + DS)")
    print("="*80)
    
    # ==================== CẤU HÌNH ====================
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    LOCATION = os.getenv("GCP_LOCATION", "global")
    CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", None)
    
    MATRIX_FILE = r"D:\Tool\CV\CV_code\MatrixQuesGen\data\input\07. SỬ 12. ma trận KSCL lần 1 (1).xlsx"
    PROMPT_TEMPLATE_TN = r"D:\Tool\CV\CV_code\MatrixQuesGen\server\src\config\prompt\TN.txt"
    PROMPT_TEMPLATE_DS = r"D:\Tool\CV\CV_code\MatrixQuesGen\server\src\config\prompt\DS.txt"
    OUTPUT_FILE = r"D:\Tool\CV\CV_code\MatrixQuesGen\data\output\questions_all.json"
    
    print(f"\n📋 CẤU HÌNH:")
    print(f"  - Project: {PROJECT_ID}")
    print(f"  - Location: {LOCATION}")
    print(f"  - Matrix: {Path(MATRIX_FILE).name}")
    print(f"  - Output: {Path(OUTPUT_FILE).name}")
    
    # ==================== KHỞI TẠO AI CLIENT ====================
    print("\n" + "="*80)
    print("🔌 KHỞI TẠO AI CLIENT")
    print("="*80)
    
    try:
        ai_client = GenAIClient(
            project_id=PROJECT_ID,
            location=LOCATION,
            credentials_path=CREDENTIALS_PATH
        )
        
        ai_client.initialize_model(
            model_name="gemini-3-pro-preview",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        print("✅ AI Client đã sẵn sàng")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo AI Client: {e}")
        return
    
    # ==================== PARSE MA TRẬN ====================
    print("\n" + "="*80)
    print("📊 PARSE MA TRẬN")
    print("="*80)
    
    parser = MatrixParser()
    parser.load_excel(MATRIX_FILE)
    
    # Parse tất cả câu hỏi theo loại
    all_questions = parser.parse_matrix()
    
    # Lấy câu hỏi TN và DS
    tn_questions = [q for q in all_questions if q.question_type == "TN"]
    
    # Group câu hỏi DS
    ds_questions = parser.group_true_false_questions()
    
    print(f"\n✅ Tổng số câu hỏi:")
    print(f"  - TN (Trắc nghiệm): {len(tn_questions)} câu")
    print(f"  - DS (Đúng/Sai): {len(ds_questions)} câu")
    
    # ==================== KHỞI TẠO GENERATOR ====================
    print("\n" + "="*80)
    print("🤖 KHỞI TẠO QUESTION GENERATOR")
    print("="*80)
    
    generator = QuestionGenerator(
        ai_client=ai_client,
        prompt_template_path=PROMPT_TEMPLATE_TN  # Default
    )
    print("✅ Generator đã sẵn sàng")
    
    # ==================== XỬ LÝ CONFIRM ====================
    print("\n" + "="*80)
    print("📝 CHUẨN BỊ SINH CÂU HỎI")
    print("="*80)
    
    print(f"\nSẽ sinh:")
    print(f"  🔹 {len(tn_questions)} câu TN")
    print(f"  🔹 {len(ds_questions)} câu DS")
    print(f"  📊 Tổng: {len(tn_questions) + len(ds_questions)} câu")
    
    print("\n❓ Bắt đầu sinh câu hỏi? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm != 'y':
        print("❌ Đã hủy")
        return
    
    # ==================== SINH CÂU HỎI TN ====================
    print("\n" + "="*80)
    print("🎯 SINH CÂU HỎI TRẮC NGHIỆM (TN)")
    print("="*80)
    
    generated_tn = []
    
    try:
        for i, tn_spec in enumerate(tn_questions, 1):
            print(f"\n[{i}/{len(tn_questions)}] Đang sinh: {tn_spec.question_codes[0] if tn_spec.question_codes else 'N/A'} - {tn_spec.lesson_name[:50]}...")
            
            questions = generator.generate_questions_for_spec(
                spec=tn_spec,
                prompt_template_path=PROMPT_TEMPLATE_TN
            )
            
            generated_tn.extend(questions)
            print(f"  ✅ Đã sinh {len(questions)} câu")
        
        print(f"\n✅ Hoàn thành sinh {len(generated_tn)} câu TN")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi sinh câu TN: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== SINH CÂU HỎI DS ====================
    print("\n" + "="*80)
    print("🎯 SINH CÂU HỎI ĐÚNG/SAI (DS)")
    print("="*80)
    
    generated_ds = []
    
    try:
        for i, ds_spec in enumerate(ds_questions, 1):
            print(f"\n[{i}/{len(ds_questions)}] Đang sinh: {ds_spec.question_code} - {ds_spec.lesson_name[:50]}...")
            
            question = generator.generate_true_false_question(
                tf_spec=ds_spec,
                prompt_template_path=PROMPT_TEMPLATE_DS
            )
            
            generated_ds.append(question)
            print(f"  ✅ Đã sinh câu với 4 mệnh đề")
        
        print(f"\n✅ Hoàn thành sinh {len(generated_ds)} câu DS")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi sinh câu DS: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== MERGE VÀ LƯU KẾT QUẢ ====================
    print("\n" + "="*80)
    print("💾 LƯU KẾT QUẢ")
    print("="*80)
    
    try:
        # Chuẩn bị dữ liệu output
        output_data = {
            "metadata": {
                "total_questions": len(generated_tn) + len(generated_ds),
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "matrix_file": Path(MATRIX_FILE).name,
                "generated_at": None  # Có thể thêm timestamp
            },
            "questions": {
                "TN": [
                    {
                        "question_code": q.question_code,
                        "question_type": q.question_type,
                        "lesson_name": q.lesson_name,
                        "level": q.level,
                        "question_stem": q.question_stem,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tn
                ],
                "DS": [
                    {
                        "question_code": q.question_code,
                        "question_type": q.question_type,
                        "lesson_name": q.lesson_name,
                        "source_text": q.source_text,
                        "statements": q.statements,
                        "explanation": q.explanation
                    }
                    for q in generated_ds
                ]
            }
        }
        
        # Tạo thư mục nếu chưa có
        output_path = Path(OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Lưu file JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Đã lưu {output_data['metadata']['total_questions']} câu hỏi vào:")
        print(f"   {output_path}")
        
        # Hiển thị tóm tắt
        print(f"\n📊 TÓNG TẮT:")
        print(f"  - TN: {output_data['metadata']['tn_count']} câu")
        print(f"  - DS: {output_data['metadata']['ds_count']} câu")
        print(f"  - Tổng: {output_data['metadata']['total_questions']} câu")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi lưu kết quả: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== HOÀN THÀNH ====================
    print("\n" + "="*80)
    print("✅ WORKFLOW HOÀN THÀNH")
    print("="*80)


if __name__ == "__main__":
    main()
