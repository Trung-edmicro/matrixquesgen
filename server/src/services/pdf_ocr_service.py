"""
PDF OCR Service using Vertex AI
Extract text content from PDF files using Google Vertex AI
"""
import os
import io
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.oauth2 import service_account


class PDFOCRService:
    """Service for OCR PDF using Vertex AI"""
    
    def __init__(self, credentials_path: str = None, project_id: str = None, location: str = 'us-central1'):
        """
        Initialize Vertex AI PDF OCR Service
        
        Args:
            credentials_path: Path to GCP service account credentials JSON
            project_id: GCP project ID
            location: GCP location (default: us-central1)
        """
        load_dotenv()
        
        self.credentials_path = credentials_path or os.getenv('GCP_CREDENTIALS_PATH')
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.location = location
        
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise ValueError(f"Invalid credentials path: {self.credentials_path}")
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID not found")
        
        # Load credentials with scopes
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Google GenAI client
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
            credentials=credentials
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using Vertex AI
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"📄 Processing PDF: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        # Read PDF file and encode to base64
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Prompt for text extraction
        prompt = """Hãy trích xuất toàn bộ nội dung văn bản từ tài liệu PDF này.

Yêu cầu:
- Giữ nguyên định dạng và cấu trúc của văn bản
- Bảo toàn các tiêu đề, đoạn văn, danh sách
- Giữ nguyên ngắt dòng và khoảng cách
- Không thêm bất kỳ giải thích hay nhận xét nào
- Chỉ trả về nội dung văn bản được trích xuất

Hãy bắt đầu trích xuất:"""
        
        print("🚀 Sending request to Vertex AI...")
        
        # Generate content
        response = self.client.models.generate_content(
            model=os.getenv('OCR_MODEL', 'gemini-2.5-flash'),
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type="application/pdf"
                )
            ]
        )
        
        extracted_text = response.text
        
        print(f"✓ Extracted {len(extracted_text)} characters")
        
        return {
            'success': True,
            'text': extracted_text,
            'file_path': pdf_path,
            'file_size': os.path.getsize(pdf_path),
            'stats': {
                'characters': len(extracted_text),
                'lines': extracted_text.count('\n') + 1,
                'words': len(extracted_text.split())
            }
        }
    
    def extract_and_save_to_markdown(self, pdf_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Extract text from PDF and save to Markdown file
        
        Args:
            pdf_path: Path to PDF file
            output_path: Output markdown file path (optional)
            
        Returns:
            Dictionary containing result information
        """
        # Extract text
        result = self.extract_text_from_pdf(pdf_path)
        
        if not result['success']:
            return result
        
        # Generate output path if not provided
        if output_path is None:
            pdf_name = Path(pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(pdf_path).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{pdf_name}_OCR_{timestamp}.md"
        
        # Create markdown content
        md_content = result['text']
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
                
        result['output_file'] = str(output_path)
        return result


def main():
    """Main function to test PDF OCR"""
    print("\n" + "="*70)
    print("  PDF OCR with Vertex AI (Gemini)")
    print("="*70 + "\n")
    
    # PDF file path
    pdf_path = r"E:\App\matrixquesgen\data\input\Bai1-LichSu.pdf"
    
    try:
        # Initialize service
        ocr_service = PDFOCRService()
        
        # Extract and save
        result = ocr_service.extract_and_save_to_markdown(pdf_path)
        
        if result['success']:
            print("\n🎉 PDF OCR completed successfully!")
            print(f"\n📄 Preview of extracted text (first 500 chars):")
            print("-" * 70)
            print(result['text'][:500])
            print("...")
            print("-" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
