"""
Document Processing Service
Handles file uploads and converts various formats to text for vector database
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Fix import issue
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grand_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grand_parent_dir)
sys.path.insert(0, parent_dir)

from werkzeug.utils import secure_filename

# File processing imports
try:
    import PyPDF2
    PDF_AVAILABLE = True
    print("✅ PyPDF2 imported successfully")
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"❌ PyPDF2 not available - PDF processing disabled: {e}")

try:
    from docx import Document
    DOCX_AVAILABLE = True
    print("✅ python-docx imported successfully")
except ImportError as e:
    DOCX_AVAILABLE = False
    print(f"❌ python-docx not available - Word processing disabled: {e}")

# Force import if available in system
if not PDF_AVAILABLE:
    try:
        import sys
        import subprocess
        result = subprocess.run([sys.executable, "-c", "import PyPDF2; print('PyPDF2 available')"], 
                              capture_output=True, text=True)
        if "PyPDF2 available" in result.stdout:
            import PyPDF2
            PDF_AVAILABLE = True
            print("✅ PyPDF2 imported via subprocess check")
    except Exception as e:
        print(f"❌ Subprocess PyPDF2 check failed: {e}")

if not DOCX_AVAILABLE:
    try:
        import sys
        import subprocess
        result = subprocess.run([sys.executable, "-c", "from docx import Document; print('docx available')"], 
                              capture_output=True, text=True)
        if "docx available" in result.stdout:
            from docx import Document
            DOCX_AVAILABLE = True
            print("✅ python-docx imported via subprocess check")
    except Exception as e:
        print(f"❌ Subprocess docx check failed: {e}")

print(f"🔍 Final status - PDF: {PDF_AVAILABLE}, DOCX: {DOCX_AVAILABLE}")

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing uploaded documents"""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword'
    }
    
    def __init__(self, upload_folder: str = "uploads"):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
        logger.info(f"📁 Document processor initialized with upload folder: {self.upload_folder}")
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS and self.SUPPORTED_EXTENSIONS[ext] is not None
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return [ext for ext, mime_type in self.SUPPORTED_EXTENSIONS.items() 
                if mime_type is not None]
    
    def save_uploaded_file(self, file) -> Tuple[bool, str, str]:
        """Save uploaded file to disk"""
        try:
            if not file or file.filename == '':
                print(f"❌ File validation failed: file={file}, filename={getattr(file, 'filename', 'N/A')}")
                return False, "No file selected", ""
            
            filename = secure_filename(file.filename)
            print(f"🔍 Processing file: {file.filename} -> {filename}")
            print(f"🔍 File type check: {self.is_supported_file(filename)}")
            print(f"🔍 Supported extensions: {self.get_supported_extensions()}")
            
            if not self.is_supported_file(filename):
                supported = ', '.join(self.get_supported_extensions())
                print(f"❌ Unsupported file type: {filename}. Supported: {supported}")
                return False, f"Unsupported file type. Supported: {supported}", ""
            
            # Create unique filename
            file_path = self.upload_folder / filename
            counter = 1
            while file_path.exists():
                name, ext = file_path.stem, file_path.suffix
                file_path = self.upload_folder / f"{name}_{counter}{ext}"
                counter += 1
            
            # Save file
            file.save(str(file_path))
            print(f"💾 File saved successfully: {file_path}")
            logger.info(f"💾 File saved: {file_path}")
            
            return True, "File uploaded successfully", str(file_path)
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            logger.error(f"❌ Error saving file: {e}")
            return False, f"Error saving file: {str(e)}", ""
    
    def extract_text_from_file(self, file_path: str) -> Tuple[bool, str, str]:
        """Extract text content from uploaded file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, "File not found", ""
            
            ext = file_path.suffix.lower()
            
            if ext == '.txt':
                return self._extract_text_txt(file_path)
            elif ext == '.pdf':
                return self._extract_text_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return self._extract_text_docx(file_path)
            else:
                return False, f"Unsupported file type: {ext}", ""
                
        except Exception as e:
            logger.error(f"❌ Error extracting text: {e}")
            return False, f"Error extracting text: {str(e)}", ""
    
    def _extract_text_txt(self, file_path: Path) -> Tuple[bool, str, str]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return True, text, "Text extracted from TXT file"
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    return True, text, f"Text extracted from TXT file (encoding: {encoding})"
                except UnicodeDecodeError:
                    continue
            return False, "", "Failed to decode TXT file with multiple encodings"
    
    def _extract_text_pdf(self, file_path: Path) -> Tuple[bool, str, str]:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            return False, "", "PDF processing not available"
        
        try:
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
            if text.strip():
                return True, text, f"Text extracted from PDF ({len(pdf_reader.pages)} pages)"
            else:
                return False, "", "No text could be extracted from PDF"
                
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return False, "", f"PDF extraction failed: {str(e)}"
    
    def _extract_text_docx(self, file_path: Path) -> Tuple[bool, str, str]:
        """Extract text from Word document"""
        if not DOCX_AVAILABLE:
            return False, "", "Word processing not available"
        
        try:
            doc = Document(file_path)
            text = ""
            
            # Extract text from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + "\t"
                    text += "\n"
            
            if text.strip():
                return True, text, "Text extracted from Word document"
            else:
                return False, "", "No text could be extracted from Word document"
                
        except Exception as e:
            logger.error(f"❌ Word extraction error: {e}")
            return False, "", f"Word extraction failed: {str(e)}"
    
    def process_uploaded_documents(self, files) -> List[Dict]:
        """Process multiple uploaded files and return results"""
        results = []
        
        for file in files:
            if file and file.filename:
                logger.info(f"📄 Processing file: {file.filename}")
                
                # Save file
                success, message, file_path = self.save_uploaded_file(file)
                if not success:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': message,
                        'text': '',
                        'file_path': ''
                    })
                    continue
                
                # Extract text
                text_success, text_content, text_message = self.extract_text_from_file(file_path)
                
                results.append({
                    'filename': file.filename,
                    'success': text_success,
                    'message': text_message,
                    'text': text_content,
                    'file_path': file_path
                })
                
                logger.info(f"✅ Processed {file.filename}: {text_message}")
        
        return results
    
    def cleanup_uploaded_files(self, file_paths: List[str]) -> None:
        """Clean up uploaded files after processing"""
        for file_path in file_paths:
            try:
                Path(file_path).unlink(missing_ok=True)
                logger.info(f"🗑️ Cleaned up: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not cleanup {file_path}: {e}")
    
    def get_upload_stats(self) -> Dict:
        """Get statistics about upload folder"""
        try:
            files = list(self.upload_folder.glob('*'))
            file_types = {}
            total_size = 0
            
            for file in files:
                if file.is_file():
                    ext = file.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                    total_size += file.stat().st_size
            
            return {
                'total_files': len(files),
                'file_types': file_types,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"❌ Error getting upload stats: {e}")
            return {}
