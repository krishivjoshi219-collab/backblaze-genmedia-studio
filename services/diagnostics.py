import importlib.metadata
import re
import logging

logger = logging.getLogger("GenMediaDiagnosticsService")

class SentinelGuard:
    def __init__(self):
        pass

    def detect_signals_matrix(self, raw_log: str) -> dict:
        """
        Extracts failure indicators present in a log.
        Returns a boolean map.
        """
        log_lower = raw_log.lower()
        return {
            "system": any(sig in log_lower for sig in ["gcc", "openssl", "failed building wheel", "libssl"]),
            "environment": any(sig in log_lower for sig in ["modulenotfounderror", "no module named"]),
            "runtime": any(sig in log_lower for sig in ["keyerror", "database_url", "connection refused", "already in use"]),
            "dependency": any(sig in log_lower for sig in ["requires", "conflict", "incompatible", "version constraint"])
        }

class ScoutParser:
    def __init__(self):
        pass

    def extract_all(self, raw_log: str) -> dict:
        """
        Scans raw terminal dumps to isolate python/pip package dependency constraints.
        """
        data = {
            "requirements": [],
            "installed": []
        }

        for line in raw_log.splitlines():
            line_clean = line.strip()

            # Inline requires
            if "requires" in line_clean.lower() and "but you have" in line_clean.lower():
                match = re.search(
                    r"requires\s+([a-zA-Z0-9_\-]+)\s*([<>=!,\d\.\-]+).*?but\s+you\s+have\s+\1\s+([\d\.]+)", 
                    line_clean, 
                    re.IGNORECASE
                )
                if match:
                    pkg = match.group(1).strip().lower()
                    specs = match.group(2).strip().replace(" ", "")
                    ver = match.group(3).strip()
                    data["requirements"].append({"package": pkg, "specifiers": specs})
                    data["installed"].append({"package": pkg, "version": ver})

            # Depends on multi-line
            elif "depends on" in line_clean.lower():
                match = re.search(r"depends\s+on\s+([a-zA-Z0-9_\-]+)\s*(.*)", line_clean, re.IGNORECASE)
                if match:
                    pkg = match.group(1).strip().lower()
                    raw_specs = match.group(2).strip()
                    clean_specs = raw_specs.replace("and", ",").replace(" ", "")
                    data["requirements"].append({"package": pkg, "specifiers": clean_specs})

            # Requested versions
            elif "user requested" in line_clean.lower():
                match = re.search(r"user\s+requested\s+([a-zA-Z0-9_\-]+)==([\d\.]+)", line_clean, re.IGNORECASE)
                if match:
                    pkg = match.group(1).strip().lower()
                    ver = match.group(2).strip()
                    data["installed"].append({"package": pkg, "version": ver})

        return data

def check_system_package_health() -> list[dict]:
    """Scans local python modules to verify GenMedia Studio Hub dependency health."""
    required_packages = [
        {"name": "streamlit", "import_name": "streamlit"},
        {"name": "genblaze", "import_name": "genblaze"},
        {"name": "genblaze-core", "import_name": "genblaze_core"},
        {"name": "genblaze-gmicloud", "import_name": "genblaze_gmicloud"},
        {"name": "b2sdk", "import_name": "b2sdk"},
        {"name": "huggingface-hub", "import_name": "huggingface_hub"},
        {"name": "requests", "import_name": "requests"},
        {"name": "pillow", "import_name": "PIL"}
    ]
    
    report = []
    for pkg in required_packages:
        package_name = pkg["name"]
        import_name = pkg["import_name"]
        try:
            # Check module loading
            __import__(import_name)
            
            # Fetch package metadata version
            try:
                ver = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError:
                try:
                    mod = __import__(import_name)
                    ver = getattr(mod, "__version__", "Installed")
                except Exception:
                    ver = "Installed"
                    
            report.append({
                "package": package_name,
                "status": "Healthy",
                "version": ver
            })
        except ImportError as e:
            logger.warning(f"Dependency package '{package_name}' could not be imported: {e}")
            report.append({
                "package": package_name,
                "status": "Missing",
                "version": "N/A"
            })
            
    return report
