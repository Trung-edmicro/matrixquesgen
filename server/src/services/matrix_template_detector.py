"""
Module phát hiện template ma trận
"""
import pandas as pd
from typing import Tuple
from enum import Enum


class MatrixTemplate(Enum):
    """Các template ma trận được hỗ trợ"""
    TEMPLATE_1 = "template_1"  # Ma trận đơn giản, chỉ có 1 sheet
    TEMPLATE_2 = "template_2"  # Ma trận + sheet câu hỏi mẫu


class MatrixTemplateDetector:
    """Class phát hiện template ma trận"""
    
    @staticmethod
    def detect(file_path: str) -> Tuple[MatrixTemplate, dict]:
        """
        Phát hiện template của file ma trận
        
        Args:
            file_path: Đường dẫn file Excel
            
        Returns:
            Tuple[MatrixTemplate, dict]: (template, metadata)
            metadata có thể chứa:
                - matrix_sheet: tên sheet chứa ma trận
                - sample_sheet: tên sheet chứa câu hỏi mẫu (nếu có)
                - has_sample_questions: có câu hỏi mẫu không
        """
        try:
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            
            metadata = {
                "matrix_sheet": None,
                "sample_sheet": None,
                "has_sample_questions": False,
                "all_sheets": sheet_names
            }
            
            # Kiểm tra xem có sheet "Câu hỏi mẫu" không
            sample_sheet_candidates = ["Câu hỏi mẫu", "Cau hoi mau", "Sample Questions"]
            sample_sheet = None
            
            for candidate in sample_sheet_candidates:
                if candidate in sheet_names:
                    sample_sheet = candidate
                    break
            
            # Tìm sheet ma trận
            matrix_sheet_candidates = ["Ma trận", "Ma tran", "Matrix"]
            matrix_sheet = None
            
            for candidate in matrix_sheet_candidates:
                if candidate in sheet_names:
                    matrix_sheet = candidate
                    break
            
            # Nếu không tìm thấy sheet tên "Ma trận", lấy sheet đầu tiên
            if not matrix_sheet:
                matrix_sheet = sheet_names[0]
            
            metadata["matrix_sheet"] = matrix_sheet
            
            if sample_sheet:
                # Template 2: Có sheet câu hỏi mẫu
                metadata["sample_sheet"] = sample_sheet
                metadata["has_sample_questions"] = True
                
                # Kiểm tra xem sheet câu hỏi mẫu có dữ liệu không
                df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
                if len(df_sample) > 1:  # Có ít nhất 1 hàng dữ liệu (ngoài header)
                    return MatrixTemplate.TEMPLATE_2, metadata
            
            # Template 1: Chỉ có ma trận
            return MatrixTemplate.TEMPLATE_1, metadata
            
        except Exception as e:
            print(f"⚠ Lỗi phát hiện template: {e}")
            # Mặc định trả về template 1
            return MatrixTemplate.TEMPLATE_1, {
                "matrix_sheet": None,
                "sample_sheet": None,
                "has_sample_questions": False,
                "error": str(e)
            }
    
    @staticmethod
    def print_detection_result(template: MatrixTemplate, metadata: dict):
        """In kết quả phát hiện"""
        print("\n" + "=" * 80)
        print("KẾT QUẢ PHÁT HIỆN TEMPLATE MA TRẬN")
        print("=" * 80)
        
        if template == MatrixTemplate.TEMPLATE_1:
            print("\n✓ Template: MẪU 1 (Ma trận đơn giản)")
            print("  Đặc điểm:")
            print("    - Chỉ có 1 sheet chứa ma trận")
            print("    - Cần file docx đề mẫu để tham khảo")
        else:
            print("\n✓ Template: MẪU 2 (Ma trận + Câu hỏi mẫu)")
            print("  Đặc điểm:")
            print("    - Sheet 'Ma trận': Cấu trúc ma trận")
            print("    - Sheet 'Câu hỏi mẫu': Ngân hàng câu hỏi mẫu")
            print("    - Có thể không cần file docx đề mẫu")
        
        print("\nMetadata:")
        print(f"  - Tất cả sheets: {metadata.get('all_sheets', [])}")
        print(f"  - Sheet ma trận: {metadata.get('matrix_sheet')}")
        if metadata.get('has_sample_questions'):
            print(f"  - Sheet câu hỏi mẫu: {metadata.get('sample_sheet')}")
        
        if 'error' in metadata:
            print(f"\n⚠ Lỗi: {metadata['error']}")

