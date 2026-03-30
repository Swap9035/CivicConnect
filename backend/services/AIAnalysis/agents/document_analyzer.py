import os
import base64
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
from langchain_mistralai import ChatMistralAI
from services.AIAnalysis.utils.config import settings

class DocumentAnalysisAgent:
    def __init__(self):
        self.llm = ChatMistralAI(
            model="mistral-small-latest",  # For text summarization
            mistral_api_key=settings.MISTRAL_API_KEY,
            temperature=0.1
        )
        self.vision_llm = ChatMistralAI(
            model="pixtral-12b-2409",  # Mistral vision model
            mistral_api_key=settings.MISTRAL_API_KEY,
            temperature=0.1
        )
    
    async def analyze_documents(self, document_paths: List[str]) -> Optional[str]:
        """
        Analyze documents: extract text from PDFs and summarize, get insights from images using Pixtral.
        Returns combined insights as a string.
        """
        insights = []
        
        for path in document_paths:
            print(f"Checking document path: {path}, exists: {os.path.exists(path)}")
            if not os.path.exists(path):
                print(f"Document path does not exist: {path}")
                continue
            
            file_ext = os.path.splitext(path)[1].lower()
            print(f"Processing file extension: {file_ext}")
            
            if file_ext == '.pdf':
                summary = await self._summarize_pdf(path)
                if summary:
                    insights.append(f"PDF Summary: {summary}")
                else:
                    print(f"Failed to summarize PDF: {path}")
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                insight = await self._analyze_image(path)
                if insight:
                    insights.append(f"Image Insight: {insight}")
                else:
                    print(f"Failed to analyze image: {path}")
        
        if insights:
            return "\n\n".join(insights)
        print("No insights generated from documents")
        return None
    
    async def _summarize_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF and generate a summary using LLM"""
        text = self._extract_pdf_text(pdf_path)
        if not text:
            print(f"No text extracted from PDF: {pdf_path}")
            return None
        
        try:
            prompt = f"Summarize the following document text in 4-5 sentences, focusing on key issues and details relevant to a municipal grievance:\n\n{text}"  # Limit text length
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            return response.content.strip()
        except Exception as e:
            print(f"Error summarizing PDF: {e}")
            return f"Extracted text summary unavailable. Raw text: {text[:500]}..."
    
    def _extract_pdf_text(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip() if text.strip() else None
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return None
    
    async def _analyze_image(self, image_path: str) -> Optional[str]:
        """Analyze image using Mistral Pixtral model"""
        try:
            # Convert image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image related to a municipal grievance. Describe what you see, any issues, damages, or relevant details that could help resolve the complaint."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = self.vision_llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return None
