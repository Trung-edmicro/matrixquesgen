import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.genai_client import GenAIClient
from services.matrix_parser import MatrixParser
from services.question_generator import QuestionGenerator
from services.concurrent_generator import (
    generate_tn_questions_parallel,
    generate_ds_questions_parallel
)
from services.docx_generator import DocxGenerator


def main():
    # ==================== CẤU HÌNH ====================
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    LOCATION = os.getenv("GCP_LOCATION", "global")
    CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", None)
    
    MATRIX_FILE = r"data\input\07. SỬ 12. ma trận KSCL lần 1 (1).xlsx"
    PROMPT_TEMPLATE_TN = r"server\src\config\prompt\TN.txt"
    PROMPT_TEMPLATE_DS = r"server\src\config\prompt\DS.txt"
    OUTPUT_DIR = r"data\output"
    
    # Tạo tên file output dựa trên input + timestamp
    matrix_filename = Path(MATRIX_FILE).stem  # Lấy tên file không có extension
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_basename = f"{matrix_filename}_{timestamp}"
    OUTPUT_JSON = str(Path(OUTPUT_DIR) / f"{output_basename}.json")
    OUTPUT_DOCX = str(Path(OUTPUT_DIR) / f"{output_basename}.docx")
    
    # Cấu hình concurrent processing
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))  # Số threads tối đa
    MIN_INTERVAL = float(os.getenv("MIN_INTERVAL", "0.2"))  # Delay tối thiểu giữa các lần BẮT ĐẦU request (giây)
    VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"  # Hiển thị logs chi tiết
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))  # Số lần retry tối đa
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))  # Delay giữa các lần retry (giây)
       
    try:
        ai_client = GenAIClient(
            project_id=PROJECT_ID,
            location=LOCATION,
            credentials_path=CREDENTIALS_PATH
        )
        
        ai_client.initialize_model(
            model_name="gemini-3-pro-preview",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
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
    
    # ==================== SINH CÂU HỎI TN (SONG SONG) ====================
    print("\n" + "="*80)
    print("🎯 SINH CÂU HỎI TRẮC NGHIỆM (TN) - SONG SONG")
    print("="*80)
    
    generated_tn = []
    
    try:
        generated_tn = generate_tn_questions_parallel(
            generator=generator,
            tn_specs=tn_questions,
            prompt_template_path=PROMPT_TEMPLATE_TN,
            max_workers=MAX_WORKERS,
            min_interval=MIN_INTERVAL,
            verbose=VERBOSE,
            max_retries=MAX_RETRIES,
            retry_delay=RETRY_DELAY
        )
        
        print(f"\n✅ Hoàn thành sinh {len(generated_tn)} câu TN")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi sinh câu TN: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== SINH CÂU HỎI DS (SONG SONG) ====================
    print("\n" + "="*80)
    print("SINH CÂU HỎI ĐÚNG/SAI (DS)")
    print("="*80)
    
    generated_ds = []
    
    try:
        generated_ds = generate_ds_questions_parallel(
            generator=generator,
            ds_specs=ds_questions,
            prompt_template_path=PROMPT_TEMPLATE_DS,
            max_workers=MAX_WORKERS,
            min_interval=MIN_INTERVAL,
            verbose=VERBOSE,
            max_retries=MAX_RETRIES,
            retry_delay=RETRY_DELAY
        )
        
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
                "generated_at": datetime.now().isoformat(),
                "timestamp": timestamp
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
        output_path = Path(OUTPUT_JSON)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Lưu file JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Đã lưu JSON: {output_path}")
        print(f"   📊 Tổng: {output_data['metadata']['total_questions']} câu")
        print(f"      - TN: {output_data['metadata']['tn_count']} câu")
        print(f"      - DS: {output_data['metadata']['ds_count']} câu")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi lưu JSON: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ==================== XUẤT FILE DOCX ====================
    print("\n" + "="*80)
    print("📄 XUẤT FILE DOCX")
    print("="*80)
    
    try:
        docx_gen = DocxGenerator()
        docx_gen.generate_questions_document(
            json_data=output_data,
            output_path=OUTPUT_DOCX
        )
        
        print(f"\n✅ Đã xuất DOCX: {OUTPUT_DOCX}")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi xuất DOCX: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== HOÀN THÀNH ====================
    print("\n" + "="*80)
    print("✅ WORKFLOW HOÀN THÀNH")
    print("="*80)


if __name__ == "__main__":
    main()
