"""
PDF Upload and Processing Service
Handles PDF upload, classification, text extraction, and mapping to lesson names
"""
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher
import pdfplumber

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_text_extractor import PDFPlumberService
from services.pdf_ocr_service import PDFOCRService
from services.matrix_parser import MatrixParser


class PDFProcessingService:
    """Service for processing PDF files and mapping to lesson names"""
    
    def __init__(self, uploads_dir: str = None):
        """
        Initialize PDF Processing Service
        
        Args:
            uploads_dir: Directory to store uploaded PDFs
        """
        if uploads_dir is None:
            # Default to data/uploads
            base_dir = Path(__file__).parent.parent.parent.parent
            uploads_dir = base_dir / "data" / "uploads"
        
        self.uploads_dir = Path(uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extraction services
        self.text_extractor = PDFPlumberService()
        self.ocr_service = PDFOCRService()
        
        # Storage for processed PDFs
        self.pdf_content_map = {}  # lesson_name -> content
        self.pdf_files_map = {}    # lesson_name -> file_path
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize lesson/file name for comparison
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name (lowercase, no special chars)
        """
        # Remove file extension
        name = Path(name).stem
        
        # Remove session_id prefix pattern (UUID_pdf_)
        # Pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx_pdf_
        import re
        name = re.sub(r'^[a-f0-9\-]{36}_pdf_', '', name, flags=re.IGNORECASE)
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove special characters, keep only alphanumeric and spaces
        name = re.sub(r'[^a-z0-9\s]', '', name)
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        return name
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        norm1 = self.normalize_name(str1)
        norm2 = self.normalize_name(str2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def is_pdf_text_based(self, pdf_path: str) -> bool:
        """
        Check if PDF is text-based or image-based
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if text-based, False if image-based
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages (or all if less than 3)
                pages_to_check = min(3, len(pdf.pages))
                
                text_chars_total = 0
                
                for i in range(pages_to_check):
                    page = pdf.pages[i]
                    text = page.extract_text()
                    
                    if text:
                        text_chars_total += len(text.strip())
                
                # If we found significant text (> 100 chars), it's text-based
                # Otherwise, it's likely image-based
                is_text = text_chars_total > 100
                
                return is_text
                
        except Exception as e:
            print(f"⚠️ Error checking PDF type: {str(e)}")
            # Default to text-based if error
            return True
    
    def match_pdf_to_lessons(self, pdf_files: List[str], lesson_names: List[str], 
                            similarity_threshold: float = 0.3) -> Dict[str, Dict]:
        """
        Match PDF files to lesson names
        
        Args:
            pdf_files: List of PDF file paths
            lesson_names: List of lesson names from matrix
            similarity_threshold: Minimum similarity to consider a match (default: 0.3)
            
        Returns:
            Dict with matching results
        """
        results = {
            'matched': {},      # lesson_name -> pdf_file
            'unmatched_pdfs': [],  # PDFs without match
            'missing_lessons': []  # Lessons without PDF
        }
        
        matched_pdfs = set()
        matched_lessons = set()
        
        print("\n" + "="*70)
        print("PDF MATCHING PROCESS")
        print("="*70)
        
        # Try to match each PDF to lessons
        for pdf_file in pdf_files:
            pdf_name = Path(pdf_file).stem
            best_match = None
            best_score = 0
            
            print(f"\n📄 Analyzing: {pdf_name}")
            
            for lesson_name in lesson_names:
                similarity = self.calculate_similarity(pdf_name, lesson_name)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = lesson_name
            
            if best_score >= similarity_threshold:
                results['matched'][best_match] = pdf_file
                matched_pdfs.add(pdf_file)
                matched_lessons.add(best_match)
                print(f"   ✓ Matched to: '{best_match}' (similarity: {best_score:.2%})")
            else:
                results['unmatched_pdfs'].append(pdf_file)
                print(f"   ✗ No match found (best: {best_score:.2%})")
        
        # Find lessons without PDF
        for lesson_name in lesson_names:
            if lesson_name not in matched_lessons:
                results['missing_lessons'].append(lesson_name)
        
        return results
    
    def process_pdf(self, pdf_path: str, lesson_name: str) -> Dict:
        """
        Process a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            lesson_name: Associated lesson name
            
        Returns:
            Processing result
        """
        print(f"\n{'='*70}")
        print(f"Processing: {Path(pdf_path).name}")
        print(f"Lesson: {lesson_name}")
        print(f"{'='*70}")
        
        # Check PDF type
        is_text_based = self.is_pdf_text_based(pdf_path)
        
        if is_text_based:
            print("📝 Type: Text-based PDF")
            print("🔧 Using: pdf_text_extractor")
            
            result = self.text_extractor.extract_text_from_pdf(pdf_path)
        else:
            print("🖼️ Type: Image-based PDF (scanned)")
            print("🔧 Using: pdf_ocr_service (Vertex AI)")
            
            result = self.ocr_service.extract_text_from_pdf(pdf_path)
        
        if result['success']:
            content = result['text']
            
            # Store in memory
            self.pdf_content_map[lesson_name] = content
            self.pdf_files_map[lesson_name] = pdf_path
            
            print(f"\n✅ Success! Extracted {len(content)} characters")
            
            return {
                'success': True,
                'lesson_name': lesson_name,
                'pdf_path': pdf_path,
                'is_text_based': is_text_based,
                'content': content,
                'stats': result.get('stats', {})
            }
        else:
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            
            return {
                'success': False,
                'lesson_name': lesson_name,
                'pdf_path': pdf_path,
                'error': result.get('error', 'Unknown error')
            }
    
    def process_multiple_pdfs_with_lessons(self, pdf_paths: List[str], lesson_names: List[str],
                                           similarity_threshold: float = 0.3) -> List[Dict]:
        """
        Process multiple PDFs and match to provided lesson names
        
        Args:
            pdf_paths: List of PDF file paths
            lesson_names: List of lesson names from matrix
            similarity_threshold: Minimum similarity to consider a match (default: 0.3)
            
        Returns:
            List of processing results with matched lessons
        """
        print("\n" + "="*70)
        print("BATCH PDF PROCESSING WITH LESSON NAMES")
        print("="*70)
        
        print(f"\u2713 Received {len(lesson_names)} lesson names")
        print(f"\u2713 Received {len(pdf_paths)} PDF files")
        
        # Match PDFs to lessons
        matching_results = self.match_pdf_to_lessons(pdf_paths, lesson_names, similarity_threshold)
        
        # Process matched PDFs
        processing_results = []
        
        print("\n" + "="*70)
        print("EXTRACTING CONTENT FROM MATCHED PDFs")
        print("="*70)
        
        for lesson_name, pdf_path in matching_results['matched'].items():
            result = self.process_pdf(pdf_path, lesson_name)
            if result['success']:
                processing_results.append({
                    'pdf_file': Path(pdf_path).name,
                    'matched_lesson': lesson_name,
                    'content': result['content'],
                    'is_text_based': result['is_text_based'],
                    'char_count': len(result['content'])
                })
        
        # Summary
        print("\n" + "="*70)
        print("PROCESSING SUMMARY")
        print("="*70)
        
        print(f"\n📊 Statistics:")
        print(f"   • Total lessons: {len(lesson_names)}")
        print(f"   • Total PDF files: {len(pdf_paths)}")
        print(f"   • Matched: {len(matching_results['matched'])}")
        print(f"   • Successfully processed: {len(processing_results)}")
        print(f"   • Unmatched PDFs: {len(matching_results['unmatched_pdfs'])}")
        print(f"   • Lessons without PDF: {len(matching_results['missing_lessons'])}")
        
        if matching_results['unmatched_pdfs']:
            print(f"\n⚠️  Unmatched PDFs:")
            for pdf in matching_results['unmatched_pdfs']:
                print(f"   - {Path(pdf).name}")
        
        if matching_results['missing_lessons']:
            print(f"\n📄 Lessons without PDF (will use Google Search):")
            for lesson in matching_results['missing_lessons'][:5]:  # Show first 5
                print(f"   - {lesson}")
            if len(matching_results['missing_lessons']) > 5:
                print(f"   ... and {len(matching_results['missing_lessons']) - 5} more")
        
        return processing_results
    
    def process_multiple_pdfs(self, pdf_files: List[str] = None, matrix_file: str = None,
                             pdf_paths: List[str] = None, lesson_names: List[str] = None,
                             sheet_name: str = "Sử 12"):
        """
        Process multiple PDFs and match to matrix
        
        Two modes:
        1. With matrix_file: pdf_files + matrix_file (auto extract lesson names)
        2. With lesson_names: pdf_paths + lesson_names (direct matching)
        
        Args:
            pdf_files: List of PDF file paths (mode 1)
            matrix_file: Path to Excel matrix file (mode 1)
            pdf_paths: List of PDF file paths (mode 2)
            lesson_names: List of lesson names (mode 2)
            sheet_name: Sheet name in matrix (mode 1 only)
            
        Returns:
            Complete processing results
        """
        # Mode 2: Direct lesson names
        if pdf_paths and lesson_names:
            return self.process_multiple_pdfs_with_lessons(pdf_paths, lesson_names)
        
        # Mode 1: Extract from matrix
        if not pdf_files or not matrix_file:
            raise ValueError("Must provide either (pdf_paths + lesson_names) or (pdf_files + matrix_file)")
        
        print("\n" + "="*70)
        print("BATCH PDF PROCESSING")
        print("="*70)
        
        # Load matrix to get lesson names
        print(f"\n📊 Loading matrix from: {matrix_file}")
        parser = MatrixParser()
        parser.load_excel(matrix_file, sheet_name)
        
        # Get all unique lesson names
        all_specs = parser.get_all_question_specs()
        lesson_names = set()
        
        for question_type in ['TN', 'DS', 'TLN']:
            for spec in all_specs[question_type]:
                if spec.lesson_name:
                    lesson_names.add(spec.lesson_name)
        
        lesson_names = sorted(list(lesson_names))
        
        print(f"✓ Found {len(lesson_names)} unique lessons in matrix")
        print(f"✓ Received {len(pdf_files)} PDF files")
        
        # Match PDFs to lessons
        matching_results = self.match_pdf_to_lessons(pdf_files, lesson_names)
        
        # Process matched PDFs
        processing_results = []
        
        print("\n" + "="*70)
        print("EXTRACTING CONTENT FROM MATCHED PDFs")
        print("="*70)
        
        for lesson_name, pdf_path in matching_results['matched'].items():
            result = self.process_pdf(pdf_path, lesson_name)
            processing_results.append(result)
        
        # Summary
        print("\n" + "="*70)
        print("PROCESSING SUMMARY")
        print("="*70)
        
        successful = sum(1 for r in processing_results if r['success'])
        failed = len(processing_results) - successful
        
        print(f"\n📊 Statistics:")
        print(f"   • Total lessons in matrix: {len(lesson_names)}")
        print(f"   • Total PDF files: {len(pdf_files)}")
        print(f"   • Matched: {len(matching_results['matched'])}")
        print(f"   • Successfully processed: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Unmatched PDFs: {len(matching_results['unmatched_pdfs'])}")
        print(f"   • Lessons without PDF: {len(matching_results['missing_lessons'])}")
        
        if matching_results['unmatched_pdfs']:
            print(f"\n⚠️ Unmatched PDF files:")
            for pdf in matching_results['unmatched_pdfs']:
                print(f"   - {Path(pdf).name}")
        
        if matching_results['missing_lessons']:
            print(f"\n⚠️ Lessons without PDF:")
            for lesson in matching_results['missing_lessons']:
                print(f"   - {lesson}")
        
        return {
            'matching': matching_results,
            'processing': processing_results,
            'content_map': self.pdf_content_map,
            'files_map': self.pdf_files_map,
            'summary': {
                'total_lessons': len(lesson_names),
                'total_pdfs': len(pdf_files),
                'matched': len(matching_results['matched']),
                'successful': successful,
                'failed': failed,
                'unmatched_pdfs': len(matching_results['unmatched_pdfs']),
                'missing_lessons': len(matching_results['missing_lessons'])
            }
        }
    
    def get_content_for_lesson(self, lesson_name: str) -> Optional[str]:
        """
        Get extracted content for a specific lesson
        
        Args:
            lesson_name: Name of the lesson
            
        Returns:
            Extracted content or None if not found
        """
        return self.pdf_content_map.get(lesson_name)
    
    def save_content_mapping(self, output_file: str = None) -> str:
        """
        Save content mapping to JSON file
        
        Args:
            output_file: Output file path (optional)
            
        Returns:
            Path to saved file
        """
        import json
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.uploads_dir.parent / "output"
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"content_mapping_{timestamp}.json"
        
        mapping_data = {
            'timestamp': datetime.now().isoformat(),
            'lessons': {}
        }
        
        for lesson_name, content in self.pdf_content_map.items():
            mapping_data['lessons'][lesson_name] = {
                'pdf_file': str(self.pdf_files_map.get(lesson_name, '')),
                'content': content,
                'content_length': len(content)
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Content mapping saved to: {output_file}")
        
        return str(output_file)


def main():
    """Test the PDF processing service"""
    
    # Example usage
    pdf_service = PDFProcessingService()
    
    # Example: Process PDFs from input directory
    input_dir = Path(__file__).parent.parent.parent.parent / "data" / "input"
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("**/*.pdf"))
    
    if not pdf_files:
        print("⚠️ No PDF files found in data/input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Matrix file
    matrix_file = input_dir / "07. SỬ 12. ma trận KSCL lần 1 (1).xlsx"
    
    if not matrix_file.exists():
        print(f"⚠️ Matrix file not found: {matrix_file}")
        return
    
    # Process all PDFs
    results = pdf_service.process_multiple_pdfs(
        pdf_files=[str(p) for p in pdf_files],
        matrix_file=str(matrix_file),
        sheet_name="Sử 12"
    )
    
    # Save mapping
    pdf_service.save_content_mapping()
    
    print("\n✅ Processing complete!")


if __name__ == "__main__":
    main()
