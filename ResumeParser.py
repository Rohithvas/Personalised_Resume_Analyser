import spacy
from pyresparser import ResumeParser
import re
from pdfminer.high_level import extract_text
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
from pyresparser import ResumeParser
from typing import Dict, List, Optional

class EnhancedResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_text(self, pdf_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def pyresparser_extract(self, pdf_path: str) -> Dict:
        try:
            parsed_data = ResumeParser(pdf_path).get_extracted_data()
            return parsed_data
        except Exception as e:
            print(f"Pyresparser extraction error: {e}")
            return {}

    def extract_name(self, text: str) -> Optional[str]:
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and not any(char.isdigit() for char in line):
                line = re.sub(r'(resume|cv|curriculum vitae|[\|].*)', '', line, flags=re.IGNORECASE)
                if len(line.split()) > 1:  # Ensures the line has more than one word
                    return line.strip()
        return None

    def extract_contact_using_re(self, text: str) -> Optional[str]:
        phone_pattern = r'(?:(?:\+?\d{1,3}[-.\s]?)?(?:\d{2,5}[-.\s]?){2,3}\d{3,4})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            phone = phone_match.group()
            phone = re.sub(r'[\s-]', '', phone)  # Clean formatting
            return phone
        return None

    def combine_skills(self, parsed_data: Dict, text: str) -> List[str]:
        skills_from_lib = parsed_data.get('skills', [])
        skills_section = self.find_section_content(text, ['skills', 'technical skills', 'key skills'])
        skills_from_text = [skill.strip() for skill in re.split(r'[,\n]', skills_section) if skill.strip()]
        return list(set(skills_from_lib + skills_from_text))  # Combine and deduplicate

    def find_section_content(self, text: str, headers: List[str]) -> str:
        text_lower = text.lower()
        for header in headers:
            header_pattern = fr'\n\s*{re.escape(header)}\s*\n'
            start_match = re.search(header_pattern, text_lower)
            if start_match:
                start_idx = start_match.end()
                end_idx = len(text)
                for common_header in headers + ['experience', 'certifications', 'achievements']:
                    pattern = fr'\n\s*{re.escape(common_header)}\s*\n'
                    match = re.search(pattern, text_lower[start_idx:])
                    if match:
                        possible_end = start_idx + match.start()
                        if possible_end < end_idx:
                            end_idx = possible_end
                return text[start_idx:end_idx].strip()
        return ""

    def parse_resume(self, pdf_path: str) -> Dict:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text = self.extract_text(pdf_path)
        parsed_data = self.pyresparser_extract(pdf_path)

        name = parsed_data.get('name') or self.extract_name(text)
        contact = parsed_data.get('mobile_number') or self.extract_contact_using_re(text)
        skills = self.combine_skills(parsed_data, text)
        education = parsed_data.get('education', [])

        results = {
            'personal_info': {
                'name': name,
                'email': parsed_data.get('email'),
                'contact': contact,
                'location': parsed_data.get('location')
            },
            'education': education,
            'skills': skills,
            'projects': self.find_section_content(text, ['projects', 'project']).split('\n')
        }

        return results
