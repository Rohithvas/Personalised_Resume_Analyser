
from ResumeParser import EnhancedResumeParser

resume_path = r"C:\Users\Rohithvas\Documents\Resume.pdf"

parser = EnhancedResumeParser()

skills = parser.parse_resume(resume_path)

print(skills)
