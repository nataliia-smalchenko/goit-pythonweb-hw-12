"""
File upload service for handling file storage in Cloudinary.

This module provides functionality for uploading and managing files
using the Cloudinary service. It handles file configuration and
URL generation for uploaded files.

The service implements secure file upload and management with proper
configuration and error handling.
"""

import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service class for file upload operations.

    This class provides methods for uploading files to Cloudinary
    and generating URLs for the uploaded files. It handles configuration
    and secure file management.

    Attributes:
        cloud_name (str): Cloudinary cloud name
        api_key (str): Cloudinary API key
        api_secret (str): Cloudinary API secret
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initialize the upload file service.

        Args:
            cloud_name (str): Cloudinary cloud name
            api_key (str): Cloudinary API key
            api_secret (str): Cloudinary API secret
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username: str) -> str:
        """
        Upload a file to Cloudinary and generate its URL.

        Args:
            file: File to upload
            username (str): Username for file identification

        Returns:
            str: URL of the uploaded file

        Note:
            Files are stored with a public ID based on the username
            and are automatically resized to 250x250 pixels.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
