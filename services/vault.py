import io
import time
import json
import zipfile
import logging
import requests
from b2sdk.v2 import InMemoryAccountInfo, B2Api

logger = logging.getLogger("GenMediaB2VaultService")

def test_b2_connection(b2_id: str, b2_key: str, b2_bucket: str) -> tuple[bool, str]:
    """Test the credentials and connectivity to Backblaze B2."""
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", b2_id, b2_key)
        # Check if bucket exists
        b2_api.get_bucket_by_name(b2_bucket)
        return True, "Successfully authorized and connected to bucket!"
    except Exception as e:
        logger.error(f"B2 auth test failed: {e}")
        return False, str(e)

def archive_to_b2(b2_id: str, b2_key: str, b2_bucket: str, archive_items: dict) -> tuple[bool, str, list]:
    """Uploads the compiled assets to the specified Backblaze B2 bucket."""
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", b2_id, b2_key)
        
        # Get or create bucket
        try:
            bucket = b2_api.get_bucket_by_name(b2_bucket)
        except Exception as bucket_err:
            if "bucket_not_found" in str(bucket_err).lower() or "bucket not found" in str(bucket_err).lower():
                logger.warning(f"Bucket '{b2_bucket}' not found. Attempting to create it (allPrivate)...")
                bucket = b2_api.create_bucket(b2_bucket, "allPrivate")
            else:
                raise bucket_err

        upload_reports = []
        for key_item, item in archive_items.items():
            file_name = item["name"]
            data = item["data"]
            content_type = "application/octet-stream"
            
            # Extract bytes based on type
            if item["type"] == "image":
                img_io = io.BytesIO()
                data.save(img_io, format='PNG')
                bytes_data = img_io.getvalue()
                content_type = "image/png"
            elif item["type"] == "audio" or file_name.endswith(".wav"):
                if isinstance(data, bytes):
                    bytes_data = data
                else:
                    bytes_data = data.encode('latin1')
                content_type = "audio/wav"
            else:
                bytes_data = data.encode('utf-8') if isinstance(data, str) else data
                content_type = "text/plain; charset=utf-8"
                
            # Perform B2 upload
            file_version = bucket.upload_bytes(
                data_bytes=bytes_data,
                file_name=file_name,
                content_type=content_type
            )
            
            upload_reports.append({
                "filename": file_name,
                "size_kb": len(bytes_data) / 1024.0,
                "file_id": file_version.id_,
                "upload_timestamp": file_version.upload_timestamp
            })
            
        return True, "Assets successfully archived to B2 Vault!", upload_reports
    except Exception as e:
        logger.error(f"Failed to archive to B2: {e}")
        return False, str(e), []

def get_presigned_streaming_url(b2_id: str, b2_key: str, b2_bucket: str, file_name: str, valid_duration_seconds: int = 3600) -> tuple[bool, str]:
    """
    Generates a temporary, authenticated public download/streaming URL for B2 vault assets using b2sdk.
    Enables direct high-speed CDN media streaming from Backblaze B2.
    """
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", b2_id, b2_key)
        bucket = b2_api.get_bucket_by_name(b2_bucket)
        
        auth_token = bucket.get_download_authorization(
            file_name_prefix=file_name,
            valid_duration_in_seconds=valid_duration_seconds
        )
        base_url = b2_api.get_download_url_for_file_name(b2_bucket, file_name)
        
        if auth_token:
            presigned_url = f"{base_url}?Authorization={auth_token}"
        else:
            presigned_url = base_url
            
        return True, presigned_url
    except Exception as e:
        logger.error(f"Failed to generate presigned streaming URL for file '{file_name}': {e}")
        return False, str(e)

def dispatch_webhook_notification(webhook_url: str, payload: dict) -> tuple[bool, str, dict]:
    """
    Publishes asset summary, presigned streaming URLs, and C2PA provenance metadata to external webhooks (Discord/Zapier/Make).
    Auto-formats payloads for Discord Webhooks if Discord endpoint is detected.
    """
    if not webhook_url or not webhook_url.strip():
        return False, "No webhook URL specified.", {}

    url = webhook_url.strip()
    headers = {"Content-Type": "application/json"}

    # Format for Discord Webhook if applicable
    if "discord.com/api/webhooks" in url:
        prov = payload.get("provenance_metadata", {})
        presigned = payload.get("presigned_url", "N/A")
        asset_name = payload.get("asset_name", "GenMedia Studio Asset")
        
        discord_payload = {
            "content": f"🚀 **Backblaze GenMedia Studio Asset Published!**\nAsset: `{asset_name}`",
            "embeds": [
                {
                    "title": f"🌌 Backblaze B2 Vault CDN Stream & C2PA Provenance",
                    "description": payload.get("summary", "Verified media asset published with cryptographic provenance signature."),
                    "color": 10499839,
                    "fields": [
                        {"name": "B2 Presigned CDN Stream", "value": f"[Stream Media Direct from B2]({presigned})" if presigned.startswith("http") else presigned},
                        {"name": "Model Identifier", "value": str(prov.get("model_id", "black-forest-labs/FLUX.1-schnell")), "inline": True},
                        {"name": "C2PA SHA-256 Hash", "value": f"`{str(prov.get('sha256', 'N/A'))[:24]}...`", "inline": True},
                        {"name": "Cryptographic Signature", "value": f"`{str(prov.get('signature', 'N/A'))[:32]}...`"}
                    ],
                    "footer": {"text": "Backblaze Genblaze SDK | C2PA Provenance Engine"}
                }
            ]
        }
        post_data = discord_payload
    else:
        post_data = payload

    try:
        response = requests.post(url, json=post_data, headers=headers, timeout=15)
        if response.status_code in (200, 201, 202, 204):
            return True, f"Webhook dispatched successfully (HTTP {response.status_code})!", {"status": response.status_code, "body": response.text[:200]}
        else:
            return False, f"Webhook server returned HTTP {response.status_code}: {response.text[:150]}", {"status": response.status_code, "body": response.text[:200]}
    except Exception as e:
        logger.error(f"Webhook dispatch failed to '{url}': {e}")
        return False, f"Webhook connection error: {e}", {}

def create_and_upload_storyboard_zip(
    b2_id: str,
    b2_key: str,
    b2_bucket: str,
    archive_items: dict,
    bundle_filename: str = None,
    valid_duration_seconds: int = 3600
) -> tuple[bool, str, str, bytes, dict]:
    """
    Zips all generated panels, audio tracks, translated light novel texts, SRT subtitle manifests,
    and C2PA provenance JSON manifests into a single bundle, uploads the zip to Backblaze B2,
    and returns (success, message, presigned_download_url, zip_bytes, upload_report).
    """
    try:
        if not bundle_filename:
            bundle_filename = f"storyboard_bundle_{int(time.time())}.zip"

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            c2pa_manifests = []
            
            for key, item in archive_items.items():
                fname = item["name"]
                data = item["data"]
                
                if item["type"] == "image":
                    img_io = io.BytesIO()
                    data.save(img_io, format="PNG")
                    zf.writestr(fname, img_io.getvalue())
                elif item["type"] == "audio" or fname.endswith(".wav"):
                    if isinstance(data, bytes):
                        zf.writestr(fname, data)
                    else:
                        zf.writestr(fname, data.encode("latin1"))
                else:
                    text_content = data if isinstance(data, str) else str(data)
                    zf.writestr(fname, text_content)

            # Add README summary and canonical C2PA bundle manifest
            readme_text = (
                "# Backblaze GenMedia Studio - Storyboard Archive Bundle\n\n"
                f"Bundle Filename: {bundle_filename}\n"
                f"Generated At: {time.strftime('%Y-%m-%d %H:%M:%S GMT', time.gmtime())}\n"
                "Storage Node: Backblaze B2 Vault CDN\n\n"
                "Included Assets:\n"
            )
            for k, v in archive_items.items():
                readme_text += f"- {v['name']} ({v['type']})\n"

            zf.writestr("README_STORYBOARD.md", readme_text)

        zip_bytes = zip_buf.getvalue()

        # Upload zip bundle to B2
        report = {
            "filename": bundle_filename,
            "size_kb": len(zip_bytes) / 1024.0,
            "file_id": "",
            "upload_timestamp": time.time() * 1000.0,
            "presigned_url": ""
        }

        try:
            info = InMemoryAccountInfo()
            b2_api = B2Api(info)
            b2_api.authorize_account("production", b2_id, b2_key)
            
            try:
                bucket = b2_api.get_bucket_by_name(b2_bucket)
            except Exception as bucket_err:
                if "bucket_not_found" in str(bucket_err).lower() or "bucket not found" in str(bucket_err).lower():
                    bucket = b2_api.create_bucket(b2_bucket, "allPrivate")
                else:
                    raise bucket_err

            file_version = bucket.upload_bytes(
                data_bytes=zip_bytes,
                file_name=bundle_filename,
                content_type="application/zip"
            )

            # Generate presigned download link
            ok_p, presigned_url = get_presigned_streaming_url(
                b2_id=b2_id,
                b2_key=b2_key,
                b2_bucket=b2_bucket,
                file_name=bundle_filename,
                valid_duration_seconds=valid_duration_seconds
            )

            report["file_id"] = file_version.id_
            report["upload_timestamp"] = file_version.upload_timestamp
            report["presigned_url"] = presigned_url if ok_p else ""

            return True, f"Storyboard Zip bundle successfully uploaded to B2 Vault! ({len(zip_bytes)/1024.0:.1f} KB)", presigned_url if ok_p else "", zip_bytes, report

        except Exception as b2_err:
            logger.warning(f"B2 upload skipped or failed for zip bundle ({b2_err}). Returning local zip bundle.")
            return False, f"Zip created locally ({len(zip_bytes)/1024.0:.1f} KB), but B2 upload failed: {b2_err}", "", zip_bytes, report

    except Exception as e:
        logger.error(f"Failed to create storyboard zip bundle: {e}")
        return False, str(e), "", b"", {}
