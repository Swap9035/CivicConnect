import os
import shutil
from typing import List
from fastapi import UploadFile
import uuid

class FileHandler:
    def __init__(self):
        self.upload_dir = "resolution_uploads"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_resolution_photos(self, files: List[UploadFile], officer_id: str, grievance_id: str) -> List[str]:
        """Save uploaded resolution photos and return file paths"""
        saved_paths = []
        
        # Create specific folder for this resolution
        resolution_folder = os.path.join(self.upload_dir, f"{grievance_id}_{officer_id}")
        os.makedirs(resolution_folder, exist_ok=True)
        
        for file in files:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(resolution_folder, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_paths.append(file_path)
        
        return saved_paths

    def get_file_url(self, file_path: str) -> str:
        """Generate URL for accessing file"""
        # TODO: Implement proper file serving or cloud storage URLs
        return f"/files/{file_path}"

file_handler = FileHandler()
