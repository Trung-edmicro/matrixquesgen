import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from ..core.google_drive_service import GoogleDriveService

# Load environment variables
load_dotenv()


@dataclass
class ContentItem:
    """Represents a content item from Google Drive"""
    id: str
    name: str
    mime_type: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessedContent:
    """Processed content structure matching the template"""
    subject: str
    grade: str
    topic: str
    data: Dict[str, Any]


class ContentAcquisitionService:
    """Service for acquiring and processing content from Google Drive"""

    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.content_types = {
            'sgv': ['_SGV', 'Sách giáo viên'],  # Check SGV first to avoid confusion with SGK
            'sgk': ['_SGK', 'Sách giáo khoa'],
            'sbt': ['_SBT', 'Sách bài tập', 'Bài tập'],
            'tn': ['_TN_', 'Trắc nghiệm'],
            'tln': ['_TLN_', 'Trắc nghiệm luận'],
            'tl': ['_TL_', 'Tự luận'],
            'ds': ['_DS_', 'Đúng sai', 'questions'],
            'sup_material': ['_sup_material'],  # Must check sup_material BEFORE material to avoid false match
            'material': ['_material', 'material', 'tư liệu', 'tài liệu']  # Material for DS text questions
        }
        # Root folder ID for educational content - should be configured
        self.root_folder_id = os.getenv('ROOT_GDRIVE_FOLDER_ID', 'root')

    def find_folder_by_path(self, path_components: List[str]) -> Optional[str]:
        """Find folder ID by navigating through path components"""
        try:
            current_folder_id = self.root_folder_id

            for component in path_components:
                # List folders in current directory
                result = self.drive_service.list_files_in_folder(
                    current_folder_id,
                    query="mimeType='application/vnd.google-apps.folder'"
                )

                if not result['success']:
                    print(f"Failed to list folders in {current_folder_id}: {result['error']}")
                    return None

                folders = result['files']
                # Find folder with matching name
                target_folder = None
                for folder in folders:
                    if folder['name'] == component:
                        target_folder = folder
                        break

                if not target_folder:
                    print(f"❌ FOLDER NOT FOUND: '{component}' not found in path {path_components}")
                    print(f"   Available folders in current location:")
                    # List available folders for debugging
                    available_result = self.drive_service.list_files_in_folder(
                        current_folder_id,
                        query="mimeType='application/vnd.google-apps.folder'"
                    )
                    if available_result['success']:
                        for folder in available_result['files'][:10]:  # Show first 10
                            print(f"   - {folder['name']}")
                        if len(available_result['files']) > 10:
                            print(f"   ... and {len(available_result['files']) - 10} more")
                    else:
                        print(f"   Could not list available folders: {available_result['error']}")
                    return None

                current_folder_id = target_folder['id']

            return current_folder_id

        except Exception as e:
            print(f"Error navigating to path {path_components}: {e}")
            return None

    def find_lesson_folder_smart(self, grade: str, subject: str, chapter: str, lesson: str, 
                                 all_lessons: List[Dict] = None) -> Optional[str]:
        """
        Smart folder finding với fallback cho 3 kiểu đặt tên:
        - Cấu trúc 1 (cũ): {SUBJECT}_KNTT_{GRADE}_{CHAPTER}_{LESSON}
          VD: HOAHOC_KNTT_C12_1_3 (Mã môn_KNTT_Mã lớp_Chương_Bài)
        - Cấu trúc 2 (mới): {SUBJECT}_KNTT_{GRADE}_{PART}_{CHAPTER}_{LESSON}
          VD: SINH_KNTT_C12_4_1_1 (Mã môn_KNTT_Mã lớp_Phần_Chương_Bài)
        - Kiểu fallback: STT bài reset mỗi chương (LICHSU_KNTT_C12_3_1 cho chương 3 bài đầu tiên)
        
        Cấu trúc Drive: C12/LICHSU/LICHSU_KNTT_C12_1_1 (flat structure)
        
        Args:
            grade: Mã lớp (C12)
            subject: Môn học (LICHSU)
            chapter: Số chương
            lesson: Số bài (theo ma trận - có thể liên tục)
            all_lessons: List tất cả bài trong ma trận để tính toán
            
        Returns:
            folder_id hoặc None
        """
        try:
            # Navigate to subject folder: grade/subject
            subject_path = [grade, subject]
            subject_folder_id = self.find_folder_by_path(subject_path)
            
            if not subject_folder_id:
                print(f"❌ Không tìm thấy thư mục môn học: {'/'.join(subject_path)}")
                return None
            
            # Get all lesson folders under subject (flat structure)
            result = self.drive_service.list_files_in_folder(
                subject_folder_id,
                query="mimeType='application/vnd.google-apps.folder'"
            )
            
            if not result['success']:
                print(f"❌ Lỗi khi list folders trong môn {subject}: {result['error']}")
                return None
            
            # Filter only lesson folders (exclude "Prompts" and other non-lesson folders)
            all_folders = result['files']
            folders = [f for f in all_folders if '_KNTT_' in f['name']]
            
            print(f"📁 Tìm thấy {len(folders)} lesson folders trong {subject} (tổng {len(all_folders)} folders)")
            if len(all_folders) <= 20:
                print(f"   Available folders: {[f['name'] for f in all_folders]}")
            
            # Step 1: Thử tìm trực tiếp với Cấu trúc 1 (cũ): {SUBJECT}_KNTT_{GRADE}_{CHAPTER}_{LESSON}
            direct_pattern = f"{subject}_KNTT_{grade}_{chapter}_{lesson}"
            print(f"🔎 Step 1: Thử Cấu trúc 1 (cũ) - '{direct_pattern}'...")
            
            for folder in folders:
                if folder['name'] == direct_pattern:
                    print(f"✅ FOUND (Cấu trúc 1): {direct_pattern}")
                    return folder['id']
            
            print(f"⚠️  Không tìm thấy với Cấu trúc 1")
            
            # Step 2: Thử tìm với Cấu trúc 2 (mới): {SUBJECT}_KNTT_{GRADE}_{PART}_{CHAPTER}_{LESSON}
            # Tìm tất cả folders có pattern *_KNTT_{GRADE}_*_{CHAPTER}_{LESSON}
            # Lưu ý: CHAPTER có thể là 0 nếu ma trận không có STT chương
            print(f"🔎 Step 2: Thử Cấu trúc 2 (mới) - tìm pattern với Phần...")
            
            for folder in folders:
                name_parts = folder['name'].split('_')
                # Pattern: SINH_KNTT_C12_4_1_1 hoặc DIALY_KNTT_C11_1_0_1 (chapter=0)
                # name_parts: ['SINH', 'KNTT', 'C12', '4', '1', '1']
                # name_parts: ['DIALY', 'KNTT', 'C11', '1', '0', '1']
                if (len(name_parts) >= 6 and 
                    name_parts[0] == subject and 
                    name_parts[1] == 'KNTT' and
                    name_parts[2] == grade and
                    name_parts[4] == chapter and  # Chương ở vị trí thứ 5 (index 4), có thể là "0"
                    name_parts[5] == lesson):     # Bài ở vị trí thứ 6 (index 5)
                    print(f"✅ FOUND (Cấu trúc 2 - Phần {name_parts[3]}, Chương {name_parts[4]}): {folder['name']}")
                    return folder['id']
            
            print(f"⚠️  Không tìm thấy với Cấu trúc 2")
            
            # Step 3: Fallback - tính toán mapping (kiểu cũ - reset mỗi chương)
            if all_lessons:
                print(f"🔎 Step 3: Fallback - Tính toán mapping với reset STT bài mỗi chương...")
                
                # Lọc lessons trong chương hiện tại
                lessons_in_chapter = [
                    l for l in all_lessons 
                    if str(l['chapter']) == str(chapter)
                ]
                
                if not lessons_in_chapter:
                    print(f"Không có bài nào trong chương {chapter}")
                    return None
                
                print(f"Lessons trong chương {chapter} (từ ma trận): {[l['lesson'] for l in lessons_in_chapter]}")
                
                # Tìm bài đầu tiên của chương (bài có số nhỏ nhất)
                first_lesson_number = min(int(l['lesson']) for l in lessons_in_chapter)
                current_lesson_number = int(lesson)
                
                # Kiểm tra lesson có trong chương không
                lesson_numbers = [int(l['lesson']) for l in lessons_in_chapter]
                if current_lesson_number not in lesson_numbers:
                    print(f"Bài {lesson} không có trong chương {chapter}")
                    return None
                
                # Tính STT trong chương dựa trên số bài (KHÔNG phải index)
                # Công thức: STT = lesson_number - first_lesson_number + 1
                # Ví dụ: Chương 3 có bài [6,7,8,10], first=6
                #   - Bài 6:  6-6+1 = 1 → _3_1
                #   - Bài 7:  7-6+1 = 2 → _3_2
                #   - Bài 8:  8-6+1 = 3 → _3_3
                #   - Bài 10: 10-6+1 = 5 → _3_5 (bỏ qua _3_4 là bài 9)
                lesson_in_chapter = current_lesson_number - first_lesson_number + 1
                print(f"Mapping: Bài {lesson} (toàn cục) → Bài {lesson_in_chapter} (trong chương {chapter})")
                print(f"         Công thức: {current_lesson_number} - {first_lesson_number} + 1 = {lesson_in_chapter}")
                
                # Find folder với pattern Cấu trúc 1: {SUBJECT}_KNTT_{GRADE}_{CHAPTER}_{lesson_in_chapter}
                fallback_pattern = f"{subject}_KNTT_{grade}_{chapter}_{lesson_in_chapter}"
                print(f"Tìm folder với pattern fallback (Cấu trúc 1): {fallback_pattern}")
                
                for folder in folders:
                    if folder['name'] == fallback_pattern:
                        print(f"✅ FOUND (Fallback Cấu trúc 1): {fallback_pattern}")
                        return folder['id']
                
                print(f"Không tìm thấy folder '{fallback_pattern}'")
                
                # Thử với Cấu trúc 2 - fallback với reset STT
                print(f"Tìm folder với pattern fallback (Cấu trúc 2 - có Phần)...")
                for folder in folders:
                    name_parts = folder['name'].split('_')
                    # Pattern: SINH_KNTT_C12_4_1_1
                    if (len(name_parts) >= 6 and 
                        name_parts[0] == subject and 
                        name_parts[1] == 'KNTT' and
                        name_parts[2] == grade and
                        name_parts[4] == chapter and  # Chương
                        name_parts[5] == str(lesson_in_chapter)):  # Bài (đã map)
                        print(f"✅ FOUND (Fallback Cấu trúc 2 - có Phần {name_parts[3]}): {folder['name']}")
                        return folder['id']
                
                print(f"Không tìm thấy folder với cả 2 cấu trúc fallback")
            
            # Không tìm thấy bằng cả 2 cách
            print(f"KHÔNG TÌM THẤY folder cho Chương {chapter}, Bài {lesson}")
            
            # Show available folders for this chapter
            chapter_folders = [f for f in folders if f'_{chapter}_' in f['name']]
            if chapter_folders:
                print(f"   Các folders có sẵn cho chương {chapter}:")
                for folder in sorted(chapter_folders, key=lambda f: f['name'])[:10]:
                    print(f"   - {folder['name']}")
            
            return None
            
        except Exception as e:
            print(f"Lỗi khi tìm folder: {e}")
            import traceback
            traceback.print_exc()
            return None

    def download_content_by_path(self, drive_path: List[str], check_version: bool = True) -> List[ContentItem]:
        """Download all content from a specific Google Drive path with version checking
        
        Args:
            drive_path: Path components to navigate to the folder
            check_version: Enable automatic version checking (default: True)
        
        Returns:
            List of ContentItem objects
        """
        try:
            # Navigate to the folder
            folder_id = self.find_folder_by_path(drive_path)
            if not folder_id:
                print(f"Could not navigate to path: {drive_path}")
                return []

            # Get all files in the folder (non-folder files only)
            result = self.drive_service.list_files_in_folder(
                folder_id,
                query="mimeType!='application/vnd.google-apps.folder'"
            )

            if not result['success']:
                print(f"Failed to list files in folder {folder_id}: {result['error']}")
                return []

            files = result['files']
            content_items = []

            for file_info in files:
                try:
                    # Download file content with version checking
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                        temp_path = temp_file.name
                    
                    # Download file to temp location with version check
                    download_result = self.drive_service.download_file(
                        file_info['id'], 
                        temp_path,
                        check_version=check_version
                    )
                    
                    content = None
                    if download_result['success']:
                        try:
                            # Read content as text
                            with open(temp_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            # If not text file, skip content
                            content = None
                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                    
                    # Add metadata about download status
                    file_metadata = file_info.copy()
                    file_metadata['download_status'] = download_result.get('status')
                    file_metadata['modified_time'] = download_result.get('modified_time')
                    
                    content_items.append(ContentItem(
                        id=file_info['id'],
                        name=file_info['name'],
                        mime_type=file_info['mimeType'],
                        content=content,
                        metadata=file_metadata
                    ))
                except Exception as e:
                    print(f"Error processing file {file_info['name']}: {e}")
                    continue

            return content_items

        except Exception as e:
            print(f"Error downloading content from path {drive_path}: {e}")
            return []

    def categorize_content(self, content_items: List[ContentItem]) -> Dict[str, List[ContentItem]]:
        """Categorize content items by type (SGK, SGV, SBT, TN, TLN, TL, DS)"""
        categorized = {
            'sgv': [],  # Sách giáo viên
            'sgk': [],  # Sách giáo khoa
            'sbt': [],
            'tn': [],
            'tln': [],
            'tl': [],
            'ds': [],
            'material': [],  # Material for DS text questions (_material.md)
            'sup_material': []  # Supplementary material for TN/TLN/TL and DS rich content (_sup_material.md)
        }

        for item in content_items:
            item_name = item.name.lower()
            content_preview = (item.content or "").lower()[:300]  # First 300 chars for content check

            # Priority 1: Filename-based categorization
            categorized_flag = False
            for content_type, keywords in self.content_types.items():
                if any(keyword.lower() in item_name for keyword in keywords):
                    categorized[content_type].append(item)
                    categorized_flag = True
                    break

            if categorized_flag:
                continue

            # Priority 2: Content-based categorization
            if any(keyword in content_preview for keyword in ['material', 'tư liệu', 'tài liệu']):
                categorized['material'].append(item)
            elif any(keyword in content_preview for keyword in ['(nb)', '(th)', '(vd)', 'trắc nghiệm']):
                categorized['tn'].append(item)
            elif any(keyword in content_preview for keyword in ['bài tập', 'sách bài tập', 'câu hỏi và bài tập']):
                categorized['sbt'].append(item)
            elif any(keyword in content_preview for keyword in ['sách giáo viên', 'hướng dẫn giáo viên']):
                categorized['sgv'].append(item)
            elif any(keyword in content_preview for keyword in ['## bài', '### bài', 'bài học', 'sách giáo khoa']):
                categorized['sgk'].append(item)
            else:
                # Default to SGK if uncertain
                categorized['sgk'].append(item)

        return categorized

    def parse_tn_from_separate_files(self, tn_content_items: List[ContentItem], subject: str, grade: str, chapter: str, lesson: str) -> Dict[str, List[str]]:
        """Parse TN content from separate NB, TH, VD files"""
        questions = {'NB': [], 'TH': [], 'VD': []}

        # Build filename pattern for this lesson
        # Expected pattern: LICHSU_KNTT_C12_3_6_TN_NB.txt, etc.
        base_pattern = f"{subject}_{grade}_{chapter}_{lesson}_TN_"

        for item in tn_content_items:
            filename = item.name
            content = item.content or ""

            if not content.strip():
                continue

            # Check filename pattern
            if '_TN_NB' in filename or filename.endswith('_TN_NB.txt'):
                # Parse NB questions
                nb_questions = self.parse_questions_from_content(content)
                questions['NB'].extend(nb_questions)
            elif '_TN_TH' in filename or filename.endswith('_TN_TH.txt'):
                # Parse TH questions
                th_questions = self.parse_questions_from_content(content)
                questions['TH'].extend(th_questions)
            elif '_TN_VD' in filename or filename.endswith('_TN_VD.txt'):
                # Parse VD questions
                vd_questions = self.parse_questions_from_content(content)
                questions['VD'].extend(vd_questions)
            # Note: If filename doesn't match any pattern, skip it (don't try to parse unknown format)

        return questions

    def parse_tln_from_separate_files(self, tln_content_items: List[ContentItem], subject: str, grade: str, chapter: str, lesson: str) -> Dict[str, List[str]]:
        """Parse TLN content from separate NB, TH, VD files (similar to TN)"""
        questions = {'NB': [], 'TH': [], 'VD': []}

        for item in tln_content_items:
            filename = item.name
            content = item.content or ""

            if not content.strip():
                continue

            # Check filename pattern for TLN
            if '_TLN_NB' in filename or filename.endswith('_TLN_NB.txt'):
                nb_questions = self.parse_questions_from_content(content)
                questions['NB'].extend(nb_questions)
            elif '_TLN_TH' in filename or filename.endswith('_TLN_TH.txt'):
                th_questions = self.parse_questions_from_content(content)
                questions['TH'].extend(th_questions)
            elif '_TLN_VD' in filename or filename.endswith('_TLN_VD.txt'):
                vd_questions = self.parse_questions_from_content(content)
                questions['VD'].extend(vd_questions)

        return questions

    def parse_tl_from_separate_files(self, tl_content_items: List[ContentItem], subject: str, grade: str, chapter: str, lesson: str) -> Dict[str, List[str]]:
        """Parse TL content from separate NB, TH, VD files (similar to TN)"""
        questions = {'NB': [], 'TH': [], 'VD': []}

        for item in tl_content_items:
            filename = item.name
            content = item.content or ""

            if not content.strip():
                continue

            # Check filename pattern for TL
            if '_TL_NB' in filename or filename.endswith('_TL_NB.txt'):
                nb_questions = self.parse_questions_from_content(content)
                questions['NB'].extend(nb_questions)
            elif '_TL_TH' in filename or filename.endswith('_TL_TH.txt'):
                th_questions = self.parse_questions_from_content(content)
                questions['TH'].extend(th_questions)
            elif '_TL_VD' in filename or filename.endswith('_TL_VD.txt'):
                vd_questions = self.parse_questions_from_content(content)
                questions['VD'].extend(vd_questions)

        return questions

    def parse_questions_from_content(self, content: str) -> List[str]:
        """Parse questions from a single TN file content"""
        questions = []

        if not content:
            return questions

        # Split by lines and process each line
        lines = content.strip().split('\n')
        current_question = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new question (starts with number and has marker)
            if re.match(r'^\d+\.', line) and ('(NB)' in line or '(TH)' in line or '(VD)' in line):
                # Save previous question if exists
                if current_question:
                    questions.append(current_question.strip())
                current_question = line
            else:
                current_question += " " + line

        # Save the last question
        if current_question:
            questions.append(current_question.strip())

        return questions

    def parse_ds_from_separate_files(self, ds_content_items: List[ContentItem], subject: str, grade: str, chapter: str, lesson: str) -> Dict[str, List[str]]:
        """Parse DS content from separate material and questions files"""
        result = {'material': [], 'questions': []}

        # Build filename pattern for this lesson
        # Expected patterns: LICHSU_KNTT_C12_3_6_material.txt/md, LICHSU_KNTT_C12_3_6_questions.txt/md, etc.
        base_pattern = f"{subject}_{grade}_{chapter}_{lesson}_"

        for item in ds_content_items:
            filename = item.name
            content = item.content or ""

            if not content.strip():
                continue

            # Check filename pattern - only match _material, not _sup_material
            # Must check for _material specifically to avoid matching _sup_material
            if ('_material' in filename.lower() and '_sup_material' not in filename.lower()) or \
               filename.endswith(('_material.txt', '_material.md')):
                # Parse material content
                materials = self.parse_material_content(content)
                result['material'].extend(materials)
            elif 'question' in filename.lower() or filename.endswith(('_questions.txt', '_questions.md')) or 'ds' in filename.lower():
                # Parse questions content using DS parsing logic
                parsed = self.parse_ds_content(content)
                result['material'].extend(parsed.get('material', []))
                result['questions'].extend(parsed.get('questions', []))
            else:
                # Fallback: try to parse based on content structure
                if 'material' in content.lower()[:200]:
                    materials = self.parse_material_content(content)
                    result['material'].extend(materials)
                else:
                    parsed = self.parse_ds_content(content)
                    result['material'].extend(parsed.get('material', []))
                    result['questions'].extend(parsed.get('questions', []))

        return result

    def parse_material_content(self, content: str) -> List[str]:
        """Parse material content with structure: material 1., material 2., etc."""
        materials = []

        if not content:
            return materials

        # Split by "material X." pattern
        material_pattern = r'(?=material \d+\.)'
        parts = re.split(material_pattern, content, flags=re.IGNORECASE)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if this part starts with "material X."
            if re.match(r'material \d+\.', part, re.IGNORECASE):
                materials.append(part)

        # If no materials found with the pattern, treat the whole content as one material
        if not materials and content.strip():
            materials.append(content.strip())

        return materials

    def parse_ds_content(self, ds_content: str) -> Dict[str, List[str]]:
        """Parse DS content into material and questions categories"""
        result = {'material': [], 'questions': []}

        if not ds_content:
            return result

        # First, try to split by "Câu X." pattern for questions
        question_pattern = r'(?=Câu \d+\.)'
        question_parts = re.split(question_pattern, ds_content)

        if len(question_parts) > 1:
            # We have multiple questions with "Câu X." prefixes
            for part in question_parts:
                part = part.strip()
                if not part:
                    continue
                if re.match(r'Câu \d+\.', part):
                    # This is a question with "Câu X." prefix
                    result['questions'].append(part)
                else:
                    # This might be material or leftover
                    if part:
                        result['material'].append(part)
        else:
            # No "Câu X." prefixes found, treat the entire content as one question
            if ds_content.strip():
                result['questions'].append(ds_content.strip())

        return result

    def build_json_structure(self, subject: str, grade: str, chapter: str, lesson: str,
                           categorized_content: Dict[str, List[ContentItem]]) -> ProcessedContent:
        """Build the complete JSON structure for a lesson matching the template"""

        # Extract content strings
        sgk_content = ""
        if categorized_content.get('sgk'):
            sgk_content = categorized_content['sgk'][0].content or ""

        sgv_content = ""
        if categorized_content.get('sgv'):
            sgv_content = categorized_content['sgv'][0].content or ""

        sbt_content = ""
        if categorized_content.get('sbt'):
            sbt_content = categorized_content['sbt'][0].content or ""

        # Extract supplementary_material from _sup_material files
        supplementary_material = ""
        if categorized_content.get('sup_material'):
            # Concatenate all sup_material files if multiple exist
            sup_material_contents = [item.content or "" for item in categorized_content['sup_material']]
            supplementary_material = "\n\n".join(sup_material_contents)
            print(f"📄 Found supplementary_material: {len(supplementary_material)} chars")

        # Parse TN content from separate files
        tn_files = categorized_content.get('tn', [])
        print(f"🔍 Parsing TN from {len(tn_files)} files")
        tn_data = self.parse_tn_from_separate_files(tn_files, subject, grade, chapter, lesson)
        print(f"   NB: {len(tn_data.get('NB', []))} questions")
        print(f"   TH: {len(tn_data.get('TH', []))} questions")
        print(f"   VD: {len(tn_data.get('VD', []))} questions")

        # Parse DS content from separate files
        # Separate: DS questions files vs material files
        ds_question_files = categorized_content.get('ds', [])
        ds_material_files = categorized_content.get('material', [])
        
        print(f"🔍 Parsing DS from {len(ds_question_files)} question files and {len(ds_material_files)} material files")
        ds_data = self.parse_ds_from_separate_files(
            ds_question_files,
            subject, grade, chapter, lesson
        )
        
        # Extract materials separately from _material files (not from _sup_material)
        ds_materials = []
        if ds_material_files:
            for material_file in ds_material_files:
                if material_file.content:
                    ds_materials.extend(self.parse_material_content(material_file.content))
        
        ds_data['material'] = ds_materials
        
        print(f"   Material: {len(ds_data.get('material', []))} items")
        print(f"   Questions: {len(ds_data.get('questions', []))} items")

        # Parse TLN content (similar to TN)
        tln_files = categorized_content.get('tln', [])
        print(f"🔍 Parsing TLN from {len(tln_files)} files")
        tln_data = self.parse_tln_from_separate_files(tln_files, subject, grade, chapter, lesson)
        print(f"   NB: {len(tln_data.get('NB', []))} questions")
        print(f"   TH: {len(tln_data.get('TH', []))} questions")
        print(f"   VD: {len(tln_data.get('VD', []))} questions")

        # Parse TL content (similar to TN)
        tl_files = categorized_content.get('tl', [])
        print(f"🔍 Parsing TL from {len(tl_files)} files")
        tl_data = self.parse_tl_from_separate_files(tl_files, subject, grade, chapter, lesson)
        print(f"   NB: {len(tl_data.get('NB', []))} questions")
        print(f"   TH: {len(tl_data.get('TH', []))} questions")
        print(f"   VD: {len(tl_data.get('VD', []))} questions")

        data = {
            "content": {
                "SGK": sgk_content,
                "SGV": sgv_content,
                "SBT": sbt_content
            },
            "supplementary_material": supplementary_material,
            "TN": tn_data,
            "DS": ds_data,
            "TLN": tln_data,
            "TL": tl_data
        }

        topic = f"{chapter}_{lesson}"

        return ProcessedContent(
            subject=subject,
            grade=grade,
            topic=topic,
            data=data
        )

    def save_processed_content(self, processed_content: ProcessedContent,
                             output_dir: Path = Path("data/content")) -> Path:
        """Save processed content to JSON file"""
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{processed_content.subject}_{processed_content.grade}_{processed_content.topic}_content.json"
        output_path = output_dir / filename

        # Convert to dict for JSON serialization (matches template structure)
        content_dict = {
            'subject': processed_content.subject,
            'grade': processed_content.grade,
            'topic': processed_content.topic,
            'data': processed_content.data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content_dict, f, ensure_ascii=False, indent=2)

        return output_path

    def process_content_for_lesson(self, subject: str, grade: str, chapter: str, lesson: str,
                                 drive_path: List[str], all_lessons: List[Dict] = None) -> Optional[ProcessedContent]:
        """
        Complete content acquisition pipeline for a single lesson
        
        Args:
            subject: Môn học (LICHSU, HOAHOC)
            grade: Mã lớp (C12)
            chapter: Số chương
            lesson: Số bài (theo ma trận)
            drive_path: Path ban đầu từ ma trận
            all_lessons: List tất cả lessons để hỗ trợ fallback
        """
        try:
            # Try smart folder finding first - use function parameters, not drive_path
            folder_id = self.find_lesson_folder_smart(
                grade=grade,
                subject=subject,
                chapter=chapter,
                lesson=lesson,
                all_lessons=all_lessons
            )
            
            if folder_id:
                # Get all files in the folder
                result = self.drive_service.list_files_in_folder(
                    folder_id,
                    query="mimeType!='application/vnd.google-apps.folder'"
                )
                
                if result['success']:
                    content_items = []
                    import tempfile
                    import os
                    
                    for file_info in result['files']:
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                                temp_path = temp_file.name
                            
                            download_result = self.drive_service.download_file(file_info['id'], temp_path)
                            
                            content = None
                            if download_result['success']:
                                try:
                                    with open(temp_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                except UnicodeDecodeError:
                                    content = None
                                finally:
                                    if os.path.exists(temp_path):
                                        os.unlink(temp_path)
                            
                            content_items.append(ContentItem(
                                id=file_info['id'],
                                name=file_info['name'],
                                mime_type=file_info['mimeType'],
                                content=content,
                                metadata=file_info
                            ))
                        except Exception as e:
                            print(f"Error processing file {file_info['name']}: {e}")
                            continue
                    
                    if content_items:
                        # Log downloaded files
                        print(f"📥 Downloaded {len(content_items)} files:")
                        for item in content_items:
                            print(f"   - {item.name} ({len(item.content or '')} chars)")
                        
                        # Categorize and process
                        categorized = self.categorize_content(content_items)
                        
                        # Log categorization results
                        print(f"📂 Categorized content:")
                        for cat, items in categorized.items():
                            print(f"   {cat}: {len(items)} files")
                            for item in items:
                                print(f"      - {item.name}")
                        
                        # Build structure
                        processed_content = self.build_json_structure(
                            subject, grade, chapter, lesson, categorized
                        )
                        
                        return processed_content
            
            # Fallback to old method if smart finding didn't work
            print(f"⚠️ Smart finding failed, trying original path method...")
            content_items = self.download_content_by_path(drive_path)
            if not content_items:
                print(f"No content found for path: {drive_path}")
                return None

            # Categorize content
            categorized = self.categorize_content(content_items)

            # Build structure
            processed_content = self.build_json_structure(
                subject, grade, chapter, lesson, categorized
            )

            return processed_content

        except Exception as e:
            print(f"Error processing content for lesson {subject}_{grade}_{chapter}_{lesson}: {e}")
            return None
    def download_prompts_from_drive(self, grade: str = "C12", subject: str = "LICHSU", curriculum: str = "KNTT") -> bool:
        """
        Download all prompts from Google Drive to local data/prompts directory
        Saves to: data/prompts/{SUBJECT}_{CURRICULUM}_{GRADE}/
        
        Args:
            grade: Grade level (e.g., "C10", "C12")
            subject: Subject name (e.g., "LICHSU")
            curriculum: Curriculum name (e.g., "KNTT")
            
        Returns:
            bool: True if successful
        """
        try:
            print(f"🔄 Đang download prompts từ Drive ({grade}/{subject}/Prompts)...")
            
            # Prompts folder path: C12/LICHSU/Prompts
            prompts_folder_path = [grade, subject, "Prompts"]
            
            # Find Prompts folder
            prompts_folder_id = self.find_folder_by_path(prompts_folder_path)
            
            if not prompts_folder_id:
                print(f"⚠️ Không tìm thấy thư mục Prompts tại {'/'.join(prompts_folder_path)}")
                print(f"→ Tự động tạo folder Prompts...")
                
                # Find parent folder (subject folder)
                parent_path = [grade, subject]
                parent_folder_id = self.find_folder_by_path(parent_path)
                
                if not parent_folder_id:
                    print(f"❌ Không tìm thấy thư mục cha: {'/'.join(parent_path)}")
                    return False
                
                # Create Prompts folder
                try:
                    if not self.drive_service.authenticate():
                        print("❌ Authentication failed")
                        return False
                    
                    file_metadata = {
                        'name': 'Prompts',
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [parent_folder_id]
                    }
                    
                    folder = self.drive_service.service.files().create(
                        body=file_metadata,
                        fields='id, name'
                    ).execute()
                    
                    prompts_folder_id = folder['id']
                    print(f"✓ Đã tạo folder Prompts: {folder['id']}")
                    print(f"⚠️ Folder Prompts trống - cần upload prompts thủ công hoặc sẽ dùng local fallback")
                    return False  # Return False to use local fallback since folder is empty
                    
                except Exception as e:
                    print(f"❌ Lỗi khi tạo folder Prompts: {e}")
                    return False
            
            print(f"✓ Tìm thấy thư mục Prompts")
            
            # List all files in Prompts folder
            result = self.drive_service.list_files_in_folder(
                prompts_folder_id,
                query="mimeType!='application/vnd.google-apps.folder'"
            )
            
            if not result['success']:
                print(f"⚠️ Lỗi khi liệt kê files: {result['error']}")
                return False
            
            files = result['files']
            if not files:
                print("⚠️ Không có file prompts nào trong thư mục")
                return False
            
            print(f"✓ Tìm thấy {len(files)} file prompts")
            
            # Create local prompts subdirectory: data/prompts/{SUBJECT}_{CURRICULUM}_{GRADE}/
            prompts_subdir_name = f"{subject}_{curriculum}_{grade}"
            
            if os.getenv('APP_DIR'):
                local_prompts_dir = Path(os.getenv('APP_DIR')) / "data" / "prompts" / prompts_subdir_name
            else:
                local_prompts_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "prompts" / prompts_subdir_name
            
            local_prompts_dir.mkdir(parents=True, exist_ok=True)
            print(f"→ Lưu vào: {local_prompts_dir}")
            
            # Download each prompt file (with automatic version checking)
            downloaded_count = 0
            updated_count = 0
            up_to_date_count = 0
            
            for file_info in files:
                file_name = file_info['name']
                local_path = local_prompts_dir / file_name
                
                try:
                    # download_file now automatically checks version
                    download_result = self.drive_service.download_file(
                        file_info['id'], 
                        str(local_path),
                        check_version=True  # Enable automatic version checking
                    )
                    
                    if download_result['success']:
                        status = download_result.get('status', 'downloaded')
                        if status == 'up_to_date':
                            print(f"  ✓ {file_name} (đã cập nhật)")
                            up_to_date_count += 1
                        else:
                            print(f"  ✓ {file_name} (mới tải)")
                            downloaded_count += 1
                            updated_count += 1
                    else:
                        print(f"  ✗ {file_name}: {download_result.get('error')}")
                        
                except Exception as e:
                    print(f"  ✗ {file_name}: {str(e)}")
            
            total_processed = downloaded_count + up_to_date_count
            if updated_count > 0:
                print(f"✓ Đã tải mới {updated_count} prompts, {up_to_date_count} prompts đã cập nhật ({total_processed}/{len(files)} tổng)")
            else:
                print(f"✓ Tất cả {up_to_date_count} prompts đã là phiên bản mới nhất")
            return total_processed > 0
            
        except Exception as e:
            print(f"⚠️ Lỗi khi download prompts: {e}")
            return False

