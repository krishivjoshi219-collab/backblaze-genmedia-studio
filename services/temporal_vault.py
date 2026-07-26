import io
import logging
from b2sdk.v2 import InMemoryAccountInfo, B2Api

logger = logging.getLogger("GenMediaTemporalVault")

def list_historical_versions(b2_id: str, b2_key: str, b2_bucket: str) -> tuple[bool, str, list]:
    """
    Queries the Backblaze B2 bucket and retrieves a list of all historical file uploads
    including versioning tokens (file IDs) sorted by upload timestamp (newest first).
    """
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", b2_id, b2_key)
        
        try:
            bucket = b2_api.get_bucket_by_name(b2_bucket)
        except Exception as e:
            if "bucket_not_found" in str(e).lower() or "bucket not found" in str(e).lower():
                return True, f"Bucket '{b2_bucket}' does not exist yet. Create it or upload assets first.", []
            raise e
            
        versions = []
        for version_info, folder_name in bucket.list_file_versions():
            # Only track active file uploads (ignore hide markers/deletions)
            if version_info.action == "upload":
                versions.append({
                    "file_name": version_info.file_name,
                    "file_id": version_info.id_,
                    "size_kb": version_info.size / 1024.0,
                    "upload_timestamp": version_info.upload_timestamp
                })
                
        # Sort chronologically descending
        versions.sort(key=lambda x: x["upload_timestamp"], reverse=True)
        return True, "Retrieved historical file versions successfully", versions
    except Exception as e:
        logger.error(f"Failed to query B2 versions: {e}")
        return False, str(e), []

def download_historical_file(b2_id: str, b2_key: str, file_id: str) -> tuple[bool, bytes]:
    """Downloads a specific historical file version from B2 by its file ID."""
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", b2_id, b2_key)
        
        downloaded = b2_api.download_file_by_id(file_id)
        bytes_io = io.BytesIO()
        downloaded.save(bytes_io)
        file_bytes = bytes_io.getvalue()
        
        return True, file_bytes
    except Exception as e:
        logger.error(f"Failed to download historical B2 file: {e}")
        return False, str(e).encode("utf-8")
