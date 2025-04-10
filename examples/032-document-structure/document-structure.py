# Document Structure
# Learn how to extract document structure and organization using Instructor. This guide demonstrates document parsing techniques for section analysis, content organization, and metadata extraction.
# Documents often contain rich structure, such as sections, subsections, and metadata, that is implicit in their formatting.
# Converting this implicit structure into explicit structured data enables better analysis, search, and information retrieval.

# Import necessary libraries
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List

# Initialize the client with instructor
client = instructor.from_openai(OpenAI())

# Define section structure
class Section(BaseModel):
    heading: str
    content: str
    subsections: List["Section"] = Field(default_factory=list)

# Important! For recursive models, we need to rebuild the model
Section.model_rebuild()

# Define document structure
class Document(BaseModel):
    title: str
    abstract: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

# Extract document structure from text
def extract_document_structure(text: str) -> Document:
    return client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "Extract the structured representation of this document, including all sections and subsections."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_model=Document
    )

# Example usage
document_text = """
# Machine Learning in Healthcare
## Authors: Jane Smith, John Doe

### Abstract
This paper explores the applications of machine learning in healthcare settings.

### Keywords
machine learning, healthcare, AI, medical diagnosis

## Introduction
Machine learning has shown promising results in healthcare applications.

### Background
Healthcare has historically been slow to adopt new technologies.

### Current Challenges
Data privacy and model interpretability remain significant challenges.

## Methods
We employed a mixed-methods approach.

## Results
Our findings indicate a 30% improvement in diagnostic accuracy.

## Discussion
These results have significant implications for clinical practice.

## Conclusion
Machine learning will continue to transform healthcare delivery.
"""

doc_structure = extract_document_structure(document_text)

# Print the document structure
print(f"Title: {doc_structure.title}")
print(f"Authors: {', '.join(doc_structure.authors)}")
if doc_structure.abstract:
    print(f"Abstract: {doc_structure.abstract}")
print(f"Keywords: {', '.join(doc_structure.keywords)}")
print("\nSections:")
for section in doc_structure.sections:
    print(f"- {section.heading}")
    for subsection in section.subsections:
        print(f"  - {subsection.heading}")

# Function to get section content by heading
def find_section(document: Document, heading: str) -> Optional[Section]:
    """Search for a section by heading in the document."""
    for section in document.sections:
        if section.heading.lower() == heading.lower():
            return section
        for subsection in section.subsections:
            if subsection.heading.lower() == heading.lower():
                return subsection
    return None

# Example of accessing specific sections
conclusion = find_section(doc_structure, "Conclusion")
if conclusion:
    print(f"\nConclusion content: {conclusion.content}")

