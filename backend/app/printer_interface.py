"""
Windows printer integration using pywin32
Auto-discover printers, send print jobs, monitor status
Note: This module only works on Windows systems
"""
import os
import sys
from typing import List, Dict, Optional
from pathlib import Path

# Only import Windows-specific modules on Windows
if sys.platform == "win32":
    import win32print
    import win32api
    import win32con
else:
    # Provide stub implementations for non-Windows systems
    win32print = None
    win32api = None
    win32con = None


def get_available_printers() -> List[Dict]:
    """
    Get list of all installed printers on Windows
    Returns list of printer info dictionaries
    """
    # Return empty list on non-Windows systems
    if sys.platform != "win32" or win32print is None:
        return []
    
    printers = []
    
    try:
        # Enumerate all printers (local and network)
        printer_enum = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        
        for printer_info in printer_enum:
            printer_name = printer_info[2]
            
            try:
                # Open printer to get detailed info
                handle = win32print.OpenPrinter(printer_name)
                printer_details = win32print.GetPrinter(handle, 2)
                
                # Determine capabilities from driver name (heuristic)
                driver_name = printer_details.get("pDriverName", "").lower()
                
                # Detect color capability
                is_color = any(keyword in driver_name for keyword in [
                    'color', 'colour', 'clj', 'clr'
                ])
                
                # Detect duplex capability (most modern printers support it)
                has_duplex = True  # Assume true, can be refined
                
                # Detect A3 capability
                supports_a3 = any(keyword in driver_name for keyword in [
                    'a3', 'wide', 'large'
                ])
                
                # Get printer status
                status = printer_details.get("Status", 0)
                if status == 0:
                    printer_status = "idle"
                elif status & win32print.PRINTER_STATUS_PRINTING:
                    printer_status = "printing"
                elif status & win32print.PRINTER_STATUS_PAUSED:
                    printer_status = "paused"
                elif status & (win32print.PRINTER_STATUS_ERROR | win32print.PRINTER_STATUS_PAPER_JAM | 
                              win32print.PRINTER_STATUS_PAPER_OUT | win32print.PRINTER_STATUS_OFFLINE):
                    printer_status = "error"
                else:
                    printer_status = "busy"
                
                printers.append({
                    "name": printer_name,
                    "driver": printer_details.get("pDriverName", "Unknown"),
                    "port": printer_details.get("pPortName", "Unknown"),
                    "status": printer_status,
                    "color": is_color,
                    "duplex": has_duplex,
                    "a4": True,  # All printers support A4
                    "a3": supports_a3,
                    "location": printer_details.get("pLocation", ""),
                    "comment": printer_details.get("pComment", ""),
                })
                
                win32print.ClosePrinter(handle)
                
            except Exception as e:
                print(f"Error getting details for {printer_name}: {e}")
                # Add basic info even if details fail
                printers.append({
                    "name": printer_name,
                    "driver": "Unknown",
                    "port": "Unknown",
                    "status": "unknown",
                    "color": False,
                    "duplex": True,
                    "a4": True,
                    "a3": False,
                    "location": "",
                    "comment": "",
                })
    
    except Exception as e:
        print(f"Error enumerating printers: {e}")
    
    return printers


def get_default_printer() -> Optional[str]:
    """Get the system default printer name"""
    if sys.platform != "win32" or win32print is None:
        return None
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def set_default_printer(printer_name: str) -> bool:
    """Set the system default printer"""
    if sys.platform != "win32" or win32print is None:
        return False
    try:
        win32print.SetDefaultPrinter(printer_name)
        return True
    except Exception as e:
        print(f"Failed to set default printer: {e}")
        return False


def print_pdf_file(printer_name: str, pdf_path: str, copies: int = 1) -> bool:
    """
    Send PDF file to printer using Adobe Reader or system default PDF viewer
    
    Args:
        printer_name: Name of the printer
        pdf_path: Full path to PDF file
        copies: Number of copies to print
    
    Returns:
        True if print job submitted successfully
    """
    if sys.platform != "win32" or win32print is None:
        print("Printing is only supported on Windows systems")
        return False
    try:
        # Verify file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Verify printer exists
        printers = [p["name"] for p in get_available_printers()]
        if printer_name not in printers:
            raise ValueError(f"Printer not found: {printer_name}")
        
        # Method 1: Try using SumatraPDF if available (best for silent printing)
        sumatra_paths = [
            r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
            r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe"
        ]
        
        for sumatra_path in sumatra_paths:
            if os.path.exists(sumatra_path):
                import subprocess
                cmd = [
                    sumatra_path,
                    "-print-to", printer_name,
                    "-silent",
                    pdf_path
                ]
                subprocess.Popen(cmd)
                return True
        
        # Method 2: Use Adobe Reader if available
        adobe_paths = [
            r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
            r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
            r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
        ]
        
        for adobe_path in adobe_paths:
            if os.path.exists(adobe_path):
                import subprocess
                cmd = [
                    adobe_path,
                    "/t", pdf_path,
                    printer_name
                ]
                subprocess.Popen(cmd)
                return True
        
        # Method 3: Use Windows default PDF handler with printto
        import subprocess
        # Get the default PDF handler
        cmd = f'rundll32.exe C:\\Windows\\System32\\shimgvw.dll,ImageView_PrintTo /pt "{pdf_path}" "{printer_name}"'
        
        # Better method: Use PowerShell to print
        ps_script = f'''
        $printer = "{printer_name}"
        $file = "{pdf_path}"
        Start-Process -FilePath $file -ArgumentList "/p /h $printer" -WindowStyle Hidden
        '''
        
        # Try using default print verb
        try:
            win32api.ShellExecute(
                0,
                "printto",
                pdf_path,
                f'"{printer_name}"',
                ".",
                0  # SW_HIDE
            )
            return True
        except Exception as e:
            print(f"ShellExecute failed: {e}")
            
            # Last resort: Use start command
            import subprocess
            subprocess.run(
                ["powershell", "-Command", f"Start-Process -FilePath '{pdf_path}' -Verb PrintTo -ArgumentList '{printer_name}' -WindowStyle Hidden"],
                capture_output=True
            )
            return True
        
    except Exception as e:
        print(f"Print error: {e}")
        return False


def get_printer_status(printer_name: str) -> Dict:
    """
    Get detailed status of a specific printer
    
    Returns dict with:
        - status: idle/printing/error/offline
        - jobs_in_queue: number of pending jobs
        - current_job: info about active job (if any)
    """
    if sys.platform != "win32" or win32print is None:
        return {
            "status": "unavailable",
            "jobs_in_queue": 0,
            "current_job": None,
            "error": "Printer status only available on Windows"
        }
    try:
        handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(handle, 2)
        
        # Get print queue
        jobs = win32print.EnumJobs(handle, 0, -1, 1)
        
        # Determine status
        status_code = printer_info.get("Status", 0)
        if status_code == 0 and len(jobs) == 0:
            status = "idle"
        elif status_code & win32print.PRINTER_STATUS_PRINTING or len(jobs) > 0:
            status = "printing"
        elif status_code & win32print.PRINTER_STATUS_PAUSED:
            status = "paused"
        elif status_code & (win32print.PRINTER_STATUS_ERROR | win32print.PRINTER_STATUS_OFFLINE):
            status = "offline"
        else:
            status = "busy"
        
        # Get current job info
        current_job = None
        if jobs:
            job = jobs[0]  # First job in queue
            current_job = {
                "job_id": job.get("JobId"),
                "document": job.get("pDocument", "Unknown"),
                "pages_printed": job.get("PagesPrinted", 0),
                "total_pages": job.get("TotalPages", 0),
                "status": job.get("Status", ""),
            }
        
        win32print.ClosePrinter(handle)
        
        return {
            "status": status,
            "jobs_in_queue": len(jobs),
            "current_job": current_job,
            "printer_info": {
                "driver": printer_info.get("pDriverName", ""),
                "port": printer_info.get("pPortName", ""),
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "jobs_in_queue": 0,
            "current_job": None
        }


def cancel_print_job(printer_name: str, job_id: int) -> bool:
    """Cancel a specific print job"""
    try:
        handle = win32print.OpenPrinter(printer_name)
        win32print.SetJob(handle, job_id, 0, None, win32print.JOB_CONTROL_CANCEL)
        win32print.ClosePrinter(handle)
        return True
    except Exception as e:
        print(f"Failed to cancel job: {e}")
        return False


def pause_printer(printer_name: str) -> bool:
    """Pause all printing on a printer"""
    try:
        handle = win32print.OpenPrinter(printer_name)
        win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PAUSE)
        win32print.ClosePrinter(handle)
        return True
    except Exception as e:
        print(f"Failed to pause printer: {e}")
        return False


def resume_printer(printer_name: str) -> bool:
    """Resume printing on a paused printer"""
    try:
        handle = win32print.OpenPrinter(printer_name)
        win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_RESUME)
        win32print.ClosePrinter(handle)
        return True
    except Exception as e:
        print(f"Failed to resume printer: {e}")
        return False


def auto_select_printer(
    printers: List[Dict],
    requires_color: bool,
    requires_a3: bool
) -> Optional[Dict]:
    """
    Automatically select best printer based on job requirements
    
    Args:
        printers: List of available printers
        requires_color: True if job needs color printing
        requires_a3: True if job needs A3 paper size
    
    Returns:
        Best matching printer dict, or None if no match
    """
    # Filter available printers (idle or printing, not offline/error)
    available = [p for p in printers if p["status"] in ["idle", "printing"]]
    
    if not available:
        return None
    
    # Filter by requirements
    candidates = available
    
    # Must support color if required
    if requires_color:
        candidates = [p for p in candidates if p["color"]]
    
    # Must support A3 if required
    if requires_a3:
        candidates = [p for p in candidates if p["a3"]]
    
    if not candidates:
        # No exact match, return any available printer
        return available[0] if available else None
    
    # Prefer idle printers over busy ones
    idle_printers = [p for p in candidates if p["status"] == "idle"]
    if idle_printers:
        return idle_printers[0]
    
    # Return first candidate
    return candidates[0]


# Test function
if __name__ == "__main__":
    print("Discovering printers...")
    printers = get_available_printers()
    
    print(f"\nFound {len(printers)} printer(s):\n")
    for p in printers:
        print(f"  • {p['name']}")
        print(f"    Driver: {p['driver']}")
        print(f"    Status: {p['status']}")
        print(f"    Color: {p['color']}, Duplex: {p['duplex']}, A3: {p['a3']}")
        print()
    
    default = get_default_printer()
    print(f"Default printer: {default}")
