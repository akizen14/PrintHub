"""
File upload, validation, conversion, and page count extraction
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
import mimetypes
from PIL import Image
from docx import Document
import tempfile

# Try different PDF libraries
try:
    from pypdf import PdfReader
    PDF_LIB = 'pypdf'
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_LIB = 'PyPDF2'
    except ImportError:
        PDF_LIB = None
        print("Warning: No PDF library available. PDF page counting will be estimated.")

# Try to import docx2pdf, fallback if not available
try:
    from docx2pdf import convert as docx_to_pdf
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False
    print("Warning: docx2pdf not available. DOCX conversion will be limited.")

# Storage configuration
UPLOAD_DIR = Path("C:/PrintHub/Orders")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# File size limit: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.jpg', '.jpeg', '.png'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png'
}


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass


def validate_file(file_path: Path, original_filename: str) -> Tuple[str, str]:
    """
    Validate uploaded file
    Returns: (file_type, mime_type)
    Raises: FileValidationError
    """
    # Check file exists
    if not file_path.exists():
        raise FileValidationError("File not found")
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise FileValidationError(f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.0f}MB")
    
    if file_size == 0:
        raise FileValidationError("File is empty")
    
    # Check extension
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check MIME type using mimetypes
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        # Fallback based on extension
        mime_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        mime_type = mime_map.get(ext, 'application/octet-stream')
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(f"Invalid file type detected: {mime_type}")
    
    return ext, mime_type


def get_pdf_page_count(pdf_path: Path) -> int:
    """Extract page count from PDF"""
    if PDF_LIB is None:
        # Fallback: estimate based on file size (rough approximation)
        file_size = pdf_path.stat().st_size
        # Very rough estimate: 50KB per page
        estimated_pages = max(1, file_size // (50 * 1024))
        return min(estimated_pages, 100)  # Cap at 100 pages
    
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as e:
        # Fallback to file size estimation
        file_size = pdf_path.stat().st_size
        estimated_pages = max(1, file_size // (50 * 1024))
        return min(estimated_pages, 100)


def convert_image_to_pdf(image_path: Path, output_path: Path) -> int:
    """
    Convert JPG/PNG to PDF
    Returns: page count (always 1 for images)
    """
    try:
        image = Image.open(image_path)
        
        # Convert to RGB if needed (PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save as PDF
        image.save(output_path, 'PDF', resolution=100.0)
        return 1
    except Exception as e:
        raise FileValidationError(f"Failed to convert image to PDF: {str(e)}")


def convert_docx_to_pdf(docx_path: Path, output_path: Path) -> int:
    """
    Convert DOCX to PDF using MS Word COM automation
    Returns: page count
    """
    try:
        # Try using docx2pdf with MS Word
        if HAS_DOCX2PDF:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                docx_to_pdf(str(docx_path), str(output_path))
                pythoncom.CoUninitialize()
                
                # Get page count from converted PDF
                return get_pdf_page_count(output_path)
            except Exception as e:
                pythoncom.CoUninitialize()
                print(f"docx2pdf failed: {e}")
                raise
        else:
            raise ImportError("docx2pdf not available")
            
    except Exception as e:
        # If docx2pdf fails, try direct COM automation
        try:
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            
            try:
                # Open Word
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                
                # Open document
                doc = word.Documents.Open(str(docx_path.absolute()))
                
                # Save as PDF
                doc.SaveAs(str(output_path.absolute()), FileFormat=17)  # 17 = PDF format
                
                # Get page count
                page_count = doc.ComputeStatistics(2)  # 2 = wdStatisticPages
                
                # Close document
                doc.Close(False)
                word.Quit()
                
                pythoncom.CoUninitialize()
                
                return max(1, page_count)
                
            except Exception as word_error:
                pythoncom.CoUninitialize()
                print(f"Word COM automation failed: {word_error}")
                
                # Last resort: reject DOCX files
                raise FileValidationError(
                    "DOCX conversion failed. Microsoft Word is not installed or not accessible. "
                    "Please upload PDF files instead, or convert your DOCX to PDF before uploading."
                )
                
        except Exception as e2:
            raise FileValidationError(
                "DOCX conversion not available. Please upload PDF files instead."
            )


def process_uploaded_file(
    file_path: Path,
    original_filename: str,
    order_id: str
) -> Tuple[Path, int]:
    """
    Process uploaded file: validate, convert to PDF if needed, extract page count
    
    Returns: (final_pdf_path, page_count)
    """
    # Validate file
    ext, mime_type = validate_file(file_path, original_filename)
    
    # Create order directory
    order_dir = UPLOAD_DIR / order_id
    order_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine final PDF path
    pdf_filename = Path(original_filename).stem + '.pdf'
    final_pdf_path = order_dir / pdf_filename
    
    # Process based on file type
    if ext == '.pdf':
        # Already PDF, just move it
        shutil.move(str(file_path), str(final_pdf_path))
        page_count = get_pdf_page_count(final_pdf_path)
    
    elif ext in ['.jpg', '.jpeg', '.png']:
        # Convert image to PDF
        page_count = convert_image_to_pdf(file_path, final_pdf_path)
        # Remove original
        file_path.unlink()
    
    elif ext == '.docx':
        # Convert DOCX to PDF
        page_count = convert_docx_to_pdf(file_path, final_pdf_path)
        # Remove original
        file_path.unlink()
    
    else:
        raise FileValidationError(f"Unsupported file type: {ext}")
    
    return final_pdf_path, page_count


def cleanup_old_files(days: int = 7):
    """
    Delete files older than specified days
    """
    import time
    from datetime import datetime, timedelta
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    deleted_count = 0
    
    for order_dir in UPLOAD_DIR.iterdir():
        if order_dir.is_dir():
            # Check directory modification time
            if order_dir.stat().st_mtime < cutoff_time:
                try:
                    shutil.rmtree(order_dir)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {order_dir}: {e}")
    
    return deleted_count


def get_file_info(order_id: str) -> Optional[dict]:
    """Get information about uploaded file for an order"""
    order_dir = UPLOAD_DIR / order_id
    
    if not order_dir.exists():
        return None
    
    # Find PDF file in order directory
    pdf_files = list(order_dir.glob("*.pdf"))
    if not pdf_files:
        return None
    
    pdf_path = pdf_files[0]
    
    return {
        "path": str(pdf_path),
        "filename": pdf_path.name,
        "size": pdf_path.stat().st_size,
        "exists": True
    }
