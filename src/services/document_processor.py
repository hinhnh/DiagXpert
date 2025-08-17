"""
Document Processing Service
Handles file uploads and converts various formats to text for vector database
Enhanced with RAG-Anything for multimodal processing
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

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

# RAG-Anything integration
try:
    from raganything import RAGAnything
    RAG_AVAILABLE = True
    print("✅ RAG-Anything imported successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"❌ RAG-Anything not available - Advanced processing disabled: {e}")

# Enhanced image processing
try:
    from PIL import Image
    IMAGE_AVAILABLE = True
    print("✅ PIL/Pillow imported successfully")
except ImportError as e:
    IMAGE_AVAILABLE = False
    print(f"❌ PIL/Pillow not available - Image processing disabled: {e}")

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

print(f"🔍 Final status - PDF: {PDF_AVAILABLE}, DOCX: {DOCX_AVAILABLE}, RAG: {RAG_AVAILABLE}, IMAGE: {IMAGE_AVAILABLE}")

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing uploaded documents with RAG-Anything integration"""
    
    # Enhanced supported file extensions
    SUPPORTED_EXTENSIONS = {
        # Text formats
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        
        # Document formats
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.rtf': 'application/rtf',
        
        # Spreadsheet formats
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.csv': 'text/csv',
        
        # Presentation formats
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.ppt': 'application/vnd.ms-powerpoint',
        
        # Image formats
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        
        # Archive formats
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed'
    }
    
    def __init__(self, upload_folder: str = "uploads"):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
        
        # Initialize RAG-Anything if available
        self.rag = None
        if RAG_AVAILABLE:
            try:
                self.rag = RAGAnything()
                print("✅ RAG-Anything initialized successfully")
            except Exception as e:
                print(f"❌ RAG-Anything initialization failed: {e}")
                self.rag = None
        
        logger.info(f"📁 Document processor initialized with upload folder: {self.upload_folder}")
        logger.info(f"🚀 RAG-Anything available: {self.rag is not None}")
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS and self.SUPPORTED_EXTENSIONS[ext] is not None
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return [ext for ext, mime_type in self.SUPPORTED_EXTENSIONS.items() 
                if mime_type is not None]
    
    def get_file_category(self, filename: str) -> str:
        """Get file category for processing strategy"""
        ext = Path(filename).suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']:
            return 'image'
        elif ext in ['.xlsx', '.xls', '.csv']:
            return 'spreadsheet'
        elif ext in ['.pptx', '.ppt']:
            return 'presentation'
        elif ext in ['.zip', '.rar']:
            return 'archive'
        elif ext in ['.pdf', '.docx', '.doc', '.rtf', '.txt', '.md']:
            return 'document'
        else:
            return 'unknown'
    
    async def process_document_advanced(self, file_path: str, output_dir: str = None) -> Dict[str, Any]:
        """Process document using RAG-Anything for advanced multimodal processing"""
        if not self.rag:
            return {"error": "RAG-Anything not available", "fallback": True}
        
        try:
            if output_dir is None:
                output_dir = str(self.upload_folder / "processed")
            
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)
            
            # Process with RAG-Anything
            result = await self.rag.process_document_complete(
                file_path=file_path,
                output_dir=output_dir,
                parse_method="auto",
                parser="mineru",
                formula=True,      # Enable formula parsing
                table=True,        # Enable table extraction
                device="cpu"       # Use CPU for compatibility
            )
            
            return {
                "success": True,
                "result": result,
                "output_dir": output_dir,
                "method": "rag_anything"
            }
            
        except Exception as e:
            logger.error(f"❌ RAG-Anything processing failed: {e}")
            return {
                "error": str(e),
                "fallback": True,
                "method": "rag_anything_failed"
            }
    
    def process_document_fallback(self, file_path: str) -> Dict[str, Any]:
        """Fallback processing for when RAG-Anything is not available"""
        try:
            file_category = self.get_file_category(file_path)
            
            if file_category == 'image':
                return self._process_image_fallback(file_path)
            elif file_category == 'spreadsheet':
                return self._process_spreadsheet_fallback(file_path)
            elif file_category == 'presentation':
                return self._process_presentation_fallback(file_path)
            elif file_category == 'document':
                return self._process_document_fallback(file_path)
            else:
                return {"error": f"Unsupported file category: {file_category}"}
                
        except Exception as e:
            logger.error(f"❌ Fallback processing failed: {e}")
            return {"error": str(e)}
    
    def _process_image_fallback(self, file_path: str) -> Dict[str, Any]:
        """Basic image processing fallback"""
        if not IMAGE_AVAILABLE:
            return {"error": "Image processing not available"}
        
        try:
            image = Image.open(file_path)
            return {
                "success": True,
                "content_type": "image",
                "dimensions": image.size,
                "mode": image.mode,
                "format": image.format,
                "text": f"Image file: {Path(file_path).name} ({image.size[0]}x{image.size[1]} {image.mode})"
            }
        except Exception as e:
            return {"error": f"Image processing failed: {e}"}
    
    def _process_spreadsheet_fallback(self, file_path: str) -> Dict[str, Any]:
        """Basic spreadsheet processing fallback"""
        try:
            # Basic CSV processing
            if file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    return {
                        "success": True,
                        "content_type": "spreadsheet",
                        "rows": len(lines),
                        "text": f"CSV file with {len(lines)} rows"
                    }
            else:
                return {"error": "Advanced spreadsheet processing requires RAG-Anything"}
        except Exception as e:
            return {"error": f"Spreadsheet processing failed: {e}"}
    
    def _process_presentation_fallback(self, file_path: str) -> Dict[str, Any]:
        """Basic presentation processing fallback"""
        return {"error": "Presentation processing requires RAG-Anything"}
    
    def _process_document_fallback(self, file_path: str) -> Dict[str, Any]:
        """Basic document processing fallback (existing logic)"""
        # Use existing text extraction methods
        return self.extract_text(file_path)
