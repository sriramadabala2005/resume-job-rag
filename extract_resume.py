import pdfplumber

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

if __name__ == "__main__":
    resume_text = extract_text_from_pdf("data/my_resume.pdf")
    print("Extracted resume text:\n")
    print(resume_text)