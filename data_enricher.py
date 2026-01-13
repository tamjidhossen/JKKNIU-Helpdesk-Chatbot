#!/usr/bin/env python3
"""
Data Enricher for JKKNIU Helpdesk Chatbot
==========================================

Generates pre-computed summary documents for aggregation queries:
- Teacher summaries with publication counts
- Department statistics
- Admission requirements matrix

These summaries are added to ChromaDB alongside the original data,
enabling direct answers to aggregation queries without multi-doc scanning.

Usage:
    python data_enricher.py
"""

import os
import re
import glob
from typing import Dict, List, Tuple
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME, DATA_DIR


class DataEnricher:
    """Analyzes existing data and creates summary documents."""
    
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        self.teacher_data_dir = os.path.join(DATA_DIR, "CSE_Teachers")
        self.processed_dir = os.path.join(DATA_DIR, "New_Data", "processed")
        
    def detect_file_type(self, content: str) -> str:
        """Detect file type from content patterns."""
        content_lower = content.lower()
        
        if "professor" in content_lower or "lecturer" in content_lower:
            if "publications" in content_lower or "journal" in content_lower:
                return "teacher"
        
        if "admission" in content_lower and "seats" in content_lower:
            return "admission"
        
        if "curriculum" in content_lower or "syllabus" in content_lower:
            return "curriculum"
        
        if "?" in content and ("how" in content_lower or "what" in content_lower):
            return "qa"
        
        return "general"
    
    def extract_teacher_info(self, file_path: str) -> Dict:
        """Extract structured info from a teacher data file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        info = {
            "name": None,
            "designation": None,
            "department": "Computer Science and Engineering",
            "email": None,
            "publications_count": 0,
            "research_areas": [],
            "courses": [],
        }
        
        # Extract name from first line (pattern: "Dr./Professor Name - Designation")
        first_line = content.split("\n")[0]
        name_match = re.search(r"^((?:Dr\.|Professor|Prof\.)\s+[\w\.\s]+?)(?:\s*-|\s*,)", first_line)
        if name_match:
            info["name"] = name_match.group(1).strip()
        
        # Extract designation
        if "Professor & Head" in first_line or "Head of" in first_line:
            info["designation"] = "Professor & Head of Department"
        elif "Professor" in first_line and "Associate" not in first_line and "Assistant" not in first_line:
            info["designation"] = "Professor"
        elif "Associate Professor" in first_line:
            info["designation"] = "Associate Professor"
        elif "Assistant Professor" in first_line:
            info["designation"] = "Assistant Professor"
        elif "Lecturer" in first_line:
            info["designation"] = "Lecturer"
        
        # Extract email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", content)
        if email_match:
            info["email"] = email_match.group(0)
        
        # Count publications (look for "Publications" headers and count entries)
        # Each publication typically has year, title, journal info
        pub_sections = re.findall(r"(?:Journal Publications|Publications|Conference Proceedings)[^:]*:?\s*\n([^\n]+)", content)
        
        # Also count by looking for common publication patterns
        journal_count = len(re.findall(r"(?:Volume|Vol\.)\s*\d+", content))
        year_citations = len(re.findall(r"\(\d{4}\)[:\.]", content))
        info["publications_count"] = max(journal_count, year_citations, len(pub_sections))
        
        # Fallback: count distinct "Publications (year)" sections
        if info["publications_count"] == 0:
            pub_headers = re.findall(r"Publications\s*\(\d{4}", content)
            info["publications_count"] = len(pub_headers)
        
        # Also count numbered publications like "1.", "2.", etc. under Publications
        numbered_pubs = re.findall(r"^\d+\.\s+[A-Z]", content, re.MULTILINE)
        if len(numbered_pubs) > info["publications_count"]:
            info["publications_count"] = len(numbered_pubs)
        
        # Extract research interests
        research_match = re.search(r"Research Interests?:\s*\n((?:[-•]\s*[^\n]+\n?)+)", content)
        if research_match:
            interests = re.findall(r"[-•]\s*([^\n]+)", research_match.group(1))
            info["research_areas"] = [i.strip() for i in interests]
        
        # Extract courses
        courses_match = re.search(r"Courses Conducted[^:]*:\s*\n((?:[-•]\s*[^\n]+\n?)+)", content)
        if courses_match:
            courses = re.findall(r"[-•]\s*(CSE\s*\d+[^,\n]*)", courses_match.group(1))
            info["courses"] = courses[:5]  # Top 5 courses
        
        return info
    
    def extract_admission_info(self, file_path: str) -> List[Dict]:
        """Extract admission requirements from admission data file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        admissions = []
        
        # Pattern: "Department Admission at JKKNIU YEAR" followed by details
        sections = re.split(r"\n(?=[A-Z][A-Za-z\s&]+ Admission at JKKNIU)", content)
        
        for section in sections:
            if not section.strip():
                continue
            
            dept_match = re.match(r"([A-Z][A-Za-z\s&]+)\s+Admission at JKKNIU", section)
            if not dept_match:
                continue
            
            dept = dept_match.group(1).strip()
            
            # Extract seats
            seats_match = re.search(r"offers?\s*(\d+)\s*seats?", section)
            seats = int(seats_match.group(1)) if seats_match else None
            
            # Extract requirements
            requirements = []
            if "Mathematics in HSC" in section:
                requirements.append("Mathematics in HSC required")
            if "Physics" in section and "Math" in section:
                req_match = re.search(r"(\d+)/25\s*in\s*(?:both\s*)?Physics and Math", section)
                if req_match:
                    requirements.append(f"Min {req_match.group(1)}/25 in Physics and Math")
            if "practical exam" in section.lower():
                requirements.append("Practical exam required")
            if "A\" grade" in section or "A grade" in section:
                grade_match = re.search(r"\"?A\"?\s*grade in\s*(\w+)", section)
                if grade_match:
                    requirements.append(f"A grade in {grade_match.group(1)} required")
            
            admissions.append({
                "department": dept,
                "seats": seats,
                "requirements": requirements,
            })
        
        return admissions
    
    def extract_education_stats(self, files_data: Dict[str, str]) -> List[Document]:
        """Extract education statistics (Alumni, Islamic Univ graduates, etc.)."""
        jkkniu_alumni = []
        islamic_univ_grads = []
        
        for filename, content in files_data.items():
            # Extract teacher name using the existing logic per file content, 
            # but we need to re-extract it here or pass it. 
            # Better to re-extract for simplicity as we have the content.
            first_line = content.split("\n")[0]
            name_match = re.search(r"^((?:Dr\.|Professor|Prof\.)\s+[\w\.\s]+?)(?:\s*-|\s*,)", first_line)
            teacher_name = name_match.group(1).strip() if name_match else "Unknown Teacher"
            
            # Simple parsing for Education section
            lines = content.split('\n')
            in_education = False
            
            for line in lines:
                if "Education:" in line:
                    in_education = True
                    continue
                if in_education and line.strip() == "":
                    # Empty line usually ends the section in these files
                    # But let's look for known next headers to be safe or just blank lines?
                    # The files show blank lines between sections.
                    in_education = False
                    continue
                
                if in_education:
                    lower_line = line.lower()
                    if "islamic university" in lower_line:
                        if teacher_name not in islamic_univ_grads:
                            islamic_univ_grads.append(teacher_name)
                    
                    if "jatiya kabi kazi nazrul islam university" in lower_line or "jkkniu" in lower_line:
                        # Ensure it's a degree
                        if any(deg in lower_line for deg in ['b.sc', 'm.sc', 'phd', 'bachelor', 'master', 'hons']):
                            if teacher_name not in jkkniu_alumni:
                                jkkniu_alumni.append(teacher_name)

        documents = []
        
        # JKKNIU Alumni Summary
        if jkkniu_alumni:
            alumni_text = "[SUMMARY] JKKNIU CSE Department Alumni\n\n"
            alumni_text += "List of faculty members who are former students of JKKNIU:\n"
            alumni_text += f"Total Alumni Faculty: {len(jkkniu_alumni)}\n\n"
            for name in jkkniu_alumni:
                alumni_text += f"- {name}\n"
            
            documents.append(Document(
                page_content=alumni_text,
                metadata={"source": "teacher_alumni", "type": "summary", "summary_type": "alumni_overview", "keywords": "alumni, former students, graduates"}
            ))
            
        # Islamic University Graduates Summary
        if islamic_univ_grads:
            iu_text = "[SUMMARY] CSE Faculty - Islamic University Graduates\n\n"
            iu_text += "List of faculty members who graduated from Islamic University:\n"
            iu_text += f"Total Islamic University Graduates: {len(islamic_univ_grads)}\n\n"
            for name in islamic_univ_grads:
                iu_text += f"- {name}\n"
                
            documents.append(Document(
                page_content=iu_text,
                metadata={"source": "islamic_university_graduates", "type": "summary", "summary_type": "islamic_univ_grads", "keywords": "islamic university, kushtia, graduates"}
            ))
            
        return documents
    
    def generate_teacher_summaries(self) -> List[Document]:
        """Generate summary documents for all teachers."""
        documents = []
        teacher_files = sorted(glob.glob(os.path.join(self.teacher_data_dir, "t*.txt")))
        
        if not teacher_files:
            print("No teacher files found")
            return documents
        
        all_teachers = []
        for file_path in teacher_files:
            info = self.extract_teacher_info(file_path)
            if info["name"]:
                all_teachers.append(info)
        
        # Sort by publication count for the summary
        all_teachers.sort(key=lambda x: x["publications_count"], reverse=True)
        
        # Create overall publication statistics summary
        pub_summary = "[SUMMARY] CSE Department Faculty Publication Statistics\n\n"
        pub_summary += "Publication count by faculty member (ranked):\n"
        for i, t in enumerate(all_teachers, 1):
            pub_summary += f"{i}. {t['name']}: {t['publications_count']} publications"
            if t['designation']:
                pub_summary += f" ({t['designation']})"
            pub_summary += "\n"
        
        total_pubs = sum(t["publications_count"] for t in all_teachers)
        pub_summary += f"\nTotal CSE faculty publications: {total_pubs}\n"
        pub_summary += f"Number of faculty members: {len(all_teachers)}\n"
        
        if all_teachers:
            pub_summary += f"\nHighest publications: {all_teachers[0]['name']} with {all_teachers[0]['publications_count']} publications\n"
        
        documents.append(Document(
            page_content=pub_summary,
            metadata={
                "source": "generated_summary",
                "summary_type": "publication_statistics",
                "entity_type": "department",
            }
        ))
        
        # Create faculty overview summary
        faculty_summary = "[SUMMARY] CSE Department Faculty Overview\n\n"
        
        # Group by designation
        profs = [t for t in all_teachers if t["designation"] and "Professor" in t["designation"] and "Assistant" not in t["designation"] and "Associate" not in t["designation"]]
        assoc_profs = [t for t in all_teachers if t["designation"] and "Associate" in t["designation"]]
        asst_profs = [t for t in all_teachers if t["designation"] and "Assistant" in t["designation"]]
        lecturers = [t for t in all_teachers if t["designation"] and "Lecturer" in t["designation"]]
        
        faculty_summary += f"Total Faculty: {len(all_teachers)}\n\n"
        faculty_summary += f"Professors ({len(profs)}):\n"
        for t in profs:
            faculty_summary += f"  - {t['name']}"
            if t["email"]:
                faculty_summary += f" ({t['email']})"
            faculty_summary += "\n"
        
        if assoc_profs:
            faculty_summary += f"\nAssociate Professors ({len(assoc_profs)}):\n"
            for t in assoc_profs:
                faculty_summary += f"  - {t['name']}\n"
        
        if asst_profs:
            faculty_summary += f"\nAssistant Professors ({len(asst_profs)}):\n"
            for t in asst_profs:
                faculty_summary += f"  - {t['name']}\n"
        
        if lecturers:
            faculty_summary += f"\nLecturers ({len(lecturers)}):\n"
            for t in lecturers:
                faculty_summary += f"  - {t['name']}\n"
        
        documents.append(Document(
            page_content=faculty_summary,
            metadata={
                "source": "generated_summary",
                "summary_type": "faculty_overview",
                "entity_type": "department",
            }
        ))
        
        # Create research areas summary
        all_research = set()
        for t in all_teachers:
            all_research.update(t["research_areas"])
        
        if all_research:
            research_summary = "[SUMMARY] CSE Department Research Areas\n\n"
            research_summary += "Research interests covered by CSE faculty:\n"
            for area in sorted(all_research):
                # Find teachers with this research area
                teachers_in_area = [t["name"] for t in all_teachers if area in t["research_areas"]]
                research_summary += f"- {area}"
                if teachers_in_area:
                    research_summary += f" ({', '.join(teachers_in_area)})"
                research_summary += "\n"
            
            documents.append(Document(
                page_content=research_summary,
                metadata={
                    "source": "generated_summary",
                    "summary_type": "research_areas",
                    "entity_type": "department",
                }
            ))
        
        return documents
    
    def generate_admission_summary(self) -> List[Document]:
        """Generate summary documents for admission requirements."""
        documents = []
        
        # Look for admission files
        admission_file = os.path.join(self.processed_dir, "JKKNIU_Admission_2025_26.txt")
        if not os.path.exists(admission_file):
            print(f"Admission file not found: {admission_file}")
            return documents
        
        admissions = self.extract_admission_info(admission_file)
        
        if not admissions:
            print("No admission data extracted")
            return documents
        
        # Create admission overview summary
        admission_summary = "[SUMMARY] JKKNIU Admission Requirements 2025-26\n\n"
        admission_summary += "Department-wise admission requirements:\n\n"
        
        for adm in admissions:
            admission_summary += f"**{adm['department']}**\n"
            if adm['seats']:
                admission_summary += f"  Seats: {adm['seats']}\n"
            if adm['requirements']:
                admission_summary += f"  Requirements: {'; '.join(adm['requirements'])}\n"
            admission_summary += "\n"
        
        # Add important general notes
        admission_summary += "\n**Important Notes:**\n"
        admission_summary += "- Engineering departments (CSE, EEE) require Mathematics in HSC\n"
        admission_summary += "- Science unit students need Higher Secondary Certificate (HSC) in Science\n"
        admission_summary += "- Humanities/Commerce students cannot directly apply to engineering programs\n"
        admission_summary += "- Admission is through GST (integrated public university entrance test)\n"
        
        documents.append(Document(
            page_content=admission_summary,
            metadata={
                "source": "generated_summary",
                "summary_type": "admission_requirements",
                "entity_type": "admission",
            }
        ))
        
        # Create eligibility inference document
        eligibility_doc = "[SUMMARY] JKKNIU CSE Admission Eligibility Guide\n\n"
        eligibility_doc += "Can you get into CSE based on your HSC background?\n\n"
        eligibility_doc += "**Science (with Higher Mathematics):** ✅ Eligible\n"
        eligibility_doc += "  - Must score minimum 07/25 in both Physics and Math in GST\n\n"
        eligibility_doc += "**Science (without Higher Mathematics):** ❌ Not Eligible\n"
        eligibility_doc += "  - CSE requires Mathematics in HSC\n\n"
        eligibility_doc += "**Humanities:** ❌ Not Eligible\n"
        eligibility_doc += "  - Humanities students typically don't have Higher Mathematics\n"
        eligibility_doc += "  - CSE is an engineering program requiring Mathematics\n\n"
        eligibility_doc += "**Commerce/Business:** ❌ Not Eligible\n"
        eligibility_doc += "  - Commerce students don't have the required science background\n\n"
        eligibility_doc += "**Alternative Departments for Humanities/Commerce:**\n"
        eligibility_doc += "  - English, Bangla, History, Philosophy (Humanities background)\n"
        eligibility_doc += "  - Accounting, Finance, Management, Marketing (Commerce background)\n"
        
        documents.append(Document(
            page_content=eligibility_doc,
            metadata={
                "source": "generated_summary",
                "summary_type": "eligibility_guide",
                "entity_type": "admission",
            }
        ))
        
        return documents
    
    def add_summaries_to_vectorstore(self, documents: List[Document]):
        """Add summary documents to the vector store."""
        if not documents:
            print("No documents to add")
            return
        
        print(f"\nAdding {len(documents)} summary documents to vector store...")
        self.vector_store.add_documents(documents=documents)
        print("✅ Summary documents added successfully")
    
    def run(self):
        """Main execution method."""
        print("🔍 Generating pre-computed summary documents...\n")
        
        all_documents = []
        
        # Generate teacher summaries
        print("📊 Processing teacher data...")
        teacher_docs = self.generate_teacher_summaries()
        
        # We need to extract raw file content for education extraction
        # Re-reading files here is inefficient but implementing a new loader represents a larger refactor
        # Let's add a helper to read files into a dict
        teacher_files_map = {}
        teacher_files = sorted(glob.glob(os.path.join(self.teacher_data_dir, "t*.txt")))
        for fpath in teacher_files:
            with open(fpath, 'r', encoding='utf-8') as f:
                teacher_files_map[os.path.basename(fpath)] = f.read()
        
        edu_docs = self.extract_education_stats(teacher_files_map)
        print(f"   Generated {len(teacher_docs)} standard teacher summaries")
        print(f"   Generated {len(edu_docs)} education/alumni summaries")
        all_documents.extend(teacher_docs)
        all_documents.extend(edu_docs)
        
        # Generate admission summaries
        print("\n📊 Processing admission data...")
        admission_docs = self.generate_admission_summary()
        print(f"   Generated {len(admission_docs)} admission summary documents")
        all_documents.extend(admission_docs)
        
        # Add all to vector store
        print(f"\n{'='*50}")
        self.add_summaries_to_vectorstore(all_documents)
        print(f"{'='*50}")
        print(f"\n✅ Total summaries added: {len(all_documents)}")
        
        # Print summary preview
        print("\n📄 Summary Documents Preview:")
        for doc in all_documents:
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"   - {doc.metadata.get('summary_type', 'unknown')}: {preview}...")


def main():
    """Main function."""
    try:
        enricher = DataEnricher()
        enricher.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
