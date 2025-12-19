"""
Module quản lý ngân hàng câu hỏi mẫu từ Excel
"""
import pandas as pd
import random
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SampleQuestion:
    """Câu hỏi mẫu"""
    stt: int  # Số thứ tự trong sheet
    lesson_name: str  # Tên bài
    question_type: str  # Dạng câu hỏi (Trắc nghiệm, Đúng Sai, Trả lời ngắn)
    cognitive_level: str  # Cấp độ (Nhận biết, Thông hiểu, Vận dụng)
    content: str  # Nội dung câu hỏi đầy đủ (bao gồm cả đáp án)
    
    def get_normalized_type(self) -> str:
        """Chuẩn hóa loại câu hỏi"""
        type_map = {
            "Trắc nghiệm": "TN",
            "Đúng Sai": "DS",
            "Trả lời ngắn": "TLN"
        }
        return type_map.get(self.question_type, self.question_type)
    
    def get_normalized_level(self) -> str:
        """Chuẩn hóa cấp độ"""
        level_map = {
            "Nhận biết": "NB",
            "Thông hiểu": "TH",
            "Vận dụng": "VD",
            "Vận dụng cao": "VDC",
            "ALL": "ALL"  # Áp dụng cho mọi cấp độ
        }
        return level_map.get(self.cognitive_level, self.cognitive_level)


class SampleQuestionBank:
    """Ngân hàng câu hỏi mẫu"""
    
    def __init__(self):
        self.questions: List[SampleQuestion] = []
        self._index: Dict[str, List[SampleQuestion]] = {}
    
    def load_from_excel(self, file_path: str, sheet_name: str = "Câu hỏi mẫu"):
        """
        Load câu hỏi mẫu từ Excel
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet chứa câu hỏi mẫu
        """
        try:
            # Kiểm tra xem file có sheet này không
            xl = pd.ExcelFile(file_path)
            if sheet_name not in xl.sheet_names:
                print(f"⚠ File không có sheet '{sheet_name}'. Bỏ qua load câu hỏi mẫu.")
                return False
            
            # Đọc sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Parse từng câu hỏi (bỏ qua header - hàng 0)
            count = 0
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                
                # Kiểm tra có đủ dữ liệu không
                if len(row) < 5:
                    continue
                
                # Bỏ qua hàng rỗng
                if pd.isna(row[0]) or pd.isna(row[4]):
                    continue
                
                try:
                    stt = int(row[0])
                    lesson_name = str(row[1]).strip() if pd.notna(row[1]) else ""
                    question_type = str(row[2]).strip() if pd.notna(row[2]) else ""
                    cognitive_level = str(row[3]).strip() if pd.notna(row[3]) else ""
                    content = str(row[4]).strip() if pd.notna(row[4]) else ""
                    
                    # Nếu cognitive_level rỗng, đặt giá trị mặc định
                    # (Đối với câu DS, có thể không có cấp độ cụ thể vì 4 mệnh đề có cấp độ khác nhau)
                    if not cognitive_level or cognitive_level == "nan":
                        cognitive_level = "ALL"  # Áp dụng cho mọi cấp độ
                    
                    # Tạo SampleQuestion
                    question = SampleQuestion(
                        stt=stt,
                        lesson_name=lesson_name,
                        question_type=question_type,
                        cognitive_level=cognitive_level,
                        content=content
                    )
                    
                    self.questions.append(question)
                    count += 1
                    
                except Exception as e:
                    print(f"⚠ Lỗi parse hàng {idx}: {e}")
                    continue
            
            # Build index
            self._build_index()
            
            print(f"✓ Đã load {count} câu hỏi mẫu từ sheet '{sheet_name}'")
            return True
            
        except Exception as e:
            print(f"⚠ Lỗi load câu hỏi mẫu: {e}")
            return False
    
    def _build_index(self):
        """Xây dựng index để tìm kiếm nhanh"""
        self._index.clear()
        
        for question in self.questions:
            # Index theo (lesson, type, level)
            key = self._make_key(
                question.lesson_name,
                question.get_normalized_type(),
                question.get_normalized_level()
            )
            
            if key not in self._index:
                self._index[key] = []
            
            self._index[key].append(question)
    
    def _make_key(self, lesson_name: str, question_type: str, cognitive_level: str) -> str:
        """Tạo key cho index"""
        # Chuẩn hóa tên bài (loại bỏ "Bài X. ")
        import re
        lesson_normalized = re.sub(r'^Bài\s+\d+\.\s*', '', lesson_name).strip()
        return f"{lesson_normalized}|{question_type}|{cognitive_level}"
    
    def find_samples(
        self,
        lesson_name: str,
        question_type: str,  # TN, DS, TLN
        cognitive_level: str,  # NB, TH, VD, VDC
        count: int = 1
    ) -> List[SampleQuestion]:
        """
        Tìm câu hỏi mẫu phù hợp
        
        Args:
            lesson_name: Tên bài
            question_type: Loại câu hỏi (TN, DS, TLN)
            cognitive_level: Cấp độ (NB, TH, VD, VDC)
            count: Số lượng câu cần tìm
            
        Returns:
            List[SampleQuestion]: Danh sách câu hỏi mẫu (random)
        """
        key = self._make_key(lesson_name, question_type, cognitive_level)
        
        candidates = self._index.get(key, [])
        
        # Nếu không tìm thấy với cấp độ cụ thể, thử tìm với ALL (cho câu DS)
        if not candidates:
            key_all = self._make_key(lesson_name, question_type, "ALL")
            candidates = self._index.get(key_all, [])
        
        if not candidates:
            # Thử tìm với tên bài đầy đủ
            for idx_key, questions in self._index.items():
                if question_type in idx_key and (cognitive_level in idx_key or "ALL" in idx_key):
                    # Kiểm tra tên bài có match không
                    for q in questions:
                        if lesson_name in q.lesson_name or q.lesson_name in lesson_name:
                            candidates.append(q)
        
        if not candidates:
            return []
        
        # Loại bỏ trùng lặp
        candidates = list({q.stt: q for q in candidates}.values())
        
        # Random chọn
        if count >= len(candidates):
            return candidates.copy()
        else:
            return random.sample(candidates, count)
    
    def get_random_sample(
        self,
        lesson_name: str,
        question_type: str,
        cognitive_level: str
    ) -> Optional[SampleQuestion]:
        """
        Lấy 1 câu hỏi mẫu ngẫu nhiên
        
        Args:
            lesson_name: Tên bài
            question_type: Loại câu hỏi (TN, DS, TLN)
            cognitive_level: Cấp độ (NB, TH, VD, VDC)
            
        Returns:
            Optional[SampleQuestion]: Câu hỏi mẫu (random) hoặc None
        """
        samples = self.find_samples(lesson_name, question_type, cognitive_level, count=1)
        return samples[0] if samples else None
    
    def has_samples(self) -> bool:
        """Kiểm tra có câu hỏi mẫu không"""
        return len(self.questions) > 0
    
    def get_statistics(self) -> Dict:
        """Thống kê câu hỏi mẫu"""
        from collections import defaultdict
        
        stats = {
            "total": len(self.questions),
            "by_type": defaultdict(int),
            "by_level": defaultdict(int),
            "by_lesson": defaultdict(int)
        }
        
        for q in self.questions:
            stats["by_type"][q.get_normalized_type()] += 1
            stats["by_level"][q.get_normalized_level()] += 1
            stats["by_lesson"][q.lesson_name] += 1
        
        return stats
    
    def print_statistics(self):
        """In thống kê"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 80)
        print("THỐNG KÊ NGÂN HÀNG CÂU HỎI MẪU")
        print("=" * 80)
        print(f"\nTổng số câu hỏi mẫu: {stats['total']}")
        
        print("\nTheo loại câu hỏi:")
        for qtype, count in sorted(stats['by_type'].items()):
            print(f"  {qtype}: {count} câu")
        
        print("\nTheo cấp độ:")
        for level, count in sorted(stats['by_level'].items()):
            print(f"  {level}: {count} câu")
        
        print("\nTheo bài:")
        for lesson, count in sorted(stats['by_lesson'].items()):
            print(f"  {lesson}: {count} câu")


# Test
if __name__ == "__main__":
    bank = SampleQuestionBank()
    
    # Load từ file mẫu 2
    file_path = r"E:\App\matrixquesgen\data\input\Ma trận (Mẫu 2).xlsx"
    bank.load_from_excel(file_path)
    
    # Thống kê
    bank.print_statistics()
    
    # Test tìm kiếm
    print("\n" + "=" * 80)
    print("TEST TÌM KIẾM")
    print("=" * 80)
    
    # Tìm câu TN-NB cho Bài 6
    print("\n1. Tìm câu TN-NB cho Bài 6:")
    samples = bank.find_samples(
        "Bài 6. Cách mạng tháng Tám - 1945",
        "TN",
        "NB",
        count=3
    )
    print(f"   Tìm thấy {len(samples)} câu:")
    for s in samples:
        print(f"   - STT {s.stt}: {s.content[:100]}...")
    
    # Tìm câu DS-VD cho Bài 7
    print("\n2. Tìm câu DS-VD cho Bài 7:")
    sample = bank.get_random_sample(
        "Bài 7. Cuộc kháng chiến chống thực dân Pháp (1945 – 1954)",
        "DS",
        "VD"
    )
    if sample:
        print(f"   STT {sample.stt}: {sample.content[:200]}...")
    else:
        print("   Không tìm thấy")
