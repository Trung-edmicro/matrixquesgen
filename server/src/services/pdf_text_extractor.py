"""
PDF Text Extraction Service using pdfplumber
Extract text content from PDF files and save to Markdown
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
import pdfplumber


class PDFPlumberService:
    """Service for extracting text from PDF using pdfplumber"""
    
    def __init__(self):
        """Initialize PDF Plumber Service"""
        load_dotenv()
    
    def extract_text_from_pdf(self, pdf_path: str, extract_tables: bool = False) -> Dict[str, Any]:
        """
        Extract text from PDF using pdfplumber
        
        Args:
            pdf_path: Path to PDF file
            extract_tables: Whether to extract tables separately
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"📄 Processing PDF: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        all_text = []
        all_tables = []
        page_count = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    
                    # Extract text from page
                    page_text = page.extract_text()
                    
                    if page_text:
                        page_text = page_text.strip()
                        
                        # Add page header
                        all_text.append(f"\n\n{'='*60}\n## Page {i+1}\n{'='*60}\n\n{page_text}")
                    else:
                        print(f"⚠️ No text found on page {i+1}")
                        all_text.append(f"\n\n{'='*60}\n## Page {i+1}\n{'='*60}\n\n[No text content]")
                    
                    # Extract tables if requested
                    if extract_tables:
                        tables = page.extract_tables()
                        if tables:
                            for j, table in enumerate(tables):
                                all_tables.append({
                                    'page': i+1,
                                    'table_index': j+1,
                                    'data': table
                                })
            
            # Combine all text
            extracted_text = "\n".join(all_text)
                        
            return {
                'success': True,
                'text': extracted_text,
                'file_path': pdf_path,
                'file_size': os.path.getsize(pdf_path),
                'pages': page_count,
                'tables': all_tables if extract_tables else None,
                'stats': {
                    'characters': len(extracted_text),
                    'lines': extracted_text.count('\n') + 1,
                    'words': len(extracted_text.split())
                }
            }
            
        except Exception as e:
            print(f"❌ Error extracting text: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': pdf_path
            }
    
    def format_table_as_markdown(self, table_data: List[List]) -> str:
        """
        Format table data as Markdown table
        
        Args:
            table_data: 2D list of table data
            
        Returns:
            Markdown formatted table string
        """
        if not table_data or len(table_data) == 0:
            return ""
        
        md_table = []
        
        # Header row
        header = table_data[0]
        md_table.append("| " + " | ".join([str(cell) if cell else "" for cell in header]) + " |")
        
        # Separator
        md_table.append("| " + " | ".join(["---" for _ in header]) + " |")
        
        # Data rows
        for row in table_data[1:]:
            md_table.append("| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |")
        
        return "\n".join(md_table)
    
    def extract_and_save_to_markdown(self, pdf_path: str, output_path: str = None, 
                                     extract_tables: bool = False) -> Dict[str, Any]:
        """
        Extract text from PDF and save to Markdown file
        
        Args:
            pdf_path: Path to PDF file
            output_path: Output markdown file path (optional)
            extract_tables: Whether to extract and format tables
            
        Returns:
            Dictionary containing result information
        """
        # Extract text
        result = self.extract_text_from_pdf(pdf_path, extract_tables=extract_tables)
        
        if not result['success']:
            return result
        
        # Generate output path if not provided
        if output_path is None:
            pdf_name = Path(pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(pdf_path).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{pdf_name}_extracted_{timestamp}.md"
        
        # Create markdown content
        md_content = result['text']
        
        # Add tables if extracted
        if extract_tables and result['tables']:
            md_content += f"\n\n---\n\n## Extracted Tables ({len(result['tables'])} total)\n\n"
            
            for table_info in result['tables']:
                md_content += f"\n### Table {table_info['table_index']} from Page {table_info['page']}\n\n"
                md_content += self.format_table_as_markdown(table_info['data'])
                md_content += "\n\n"
                
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"\n✅ SUCCESS!")
        print(f"📝 Output saved to: {output_path}")
        print(f"📊 Statistics:")
        print(f"   • Pages: {result['pages']}")
        print(f"   • Characters: {result['stats']['characters']:,}")
        print(f"   • Words: {result['stats']['words']:,}")
        print(f"   • Lines: {result['stats']['lines']:,}")
        if extract_tables and result['tables']:
            print(f"   • Tables: {len(result['tables'])}")
        
        result['output_file'] = str(output_path)
        return result


def main():
    """Main function to test PDF text extraction"""
    print("\n" + "="*70)
    print("  PDF Text Extraction with pdfplumber")
    print("="*70 + "\n")
    
    # PDF file path
    pdf_path = r"E:\App\matrixquesgen\data\input\Bai1-LichSu.pdf"
    
    try:
        # Initialize service
        pdf_service = PDFPlumberService()
        
        # Extract and save (with tables if needed)
        result = pdf_service.extract_and_save_to_markdown(
            pdf_path, 
            extract_tables=True  # Set to True to extract tables
        )
        
        if result['success']:
            print("\n🎉 PDF text extraction completed successfully!")
            print(f"\n📄 Preview of extracted text (first 500 chars):")
            print("-" * 70)
            print(result['text'][:500])
            print("...")
            print("-" * 70)
        else:
            print(f"\n❌ Extraction failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
