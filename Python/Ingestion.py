from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re
import ast
from typing import List
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import pprint
import os
import json

poppler_path = r'' # <- Đường dẫn tới file poppler


# Convert each PDF page to an image
def convert_pdf_to_img(pdf_path, dpi=100, img_dir = "pages_img"):
    print("Converting PDF to images...")
    pages = convert_from_path(pdf_path, dpi=dpi)
    for idx, page in enumerate(pages, start=1):
        img_path = os.path.join(img_dir, f"page_{idx:02d}.png")
        page.save(img_path, "PNG")
        print(f" Saved {img_path}")


# Run OCR on each image
def applyOCR(img_dir, ocr_dir):
    print("\nRunning OCR on images...")
    for img_file in sorted(os.listdir(img_dir)):
        img_path = os.path.join(img_dir, img_file)
        text = pytesseract.image_to_string(Image.open(img_path), lang="eng")

        txt_filename = os.path.splitext(img_file)[0] + ".txt"
        txt_path = os.path.join(ocr_dir, txt_filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f" OCR output saved to {txt_path}")

        return text

def text_processing(raw_text: str):
    """
    Clean & normalize the raw OCR text
    Return: cleaned text
    """
    # Noise Removal
    text = re.sub(r"(?mi)^page\s*\d+\s*(?:of\s*\d+)?\s*$", "", raw_text)
    text = re.sub(r"[-_]{2,}", "", text)

    # Whitespace normalization
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\t", " ")
    text = text.replace("\n\n", "\n")
    return text


def extract_resume_sections(
    text: str,
    model_name: str,
    sections: List[str] = None,
):
    """
    Send the raw resume text to Ollama via LangChain, ask it to split into sections,
    and parse the JSON response into a Python dict.

    Args:
        text: Full resume text (after OCR).
        model_name: Ollama model name (e.g. "llama3", "mistral").
        sections: Optional list of section names you expect. If provided, the prompt
                  will ask the model to output exactly these keys.

    Returns:
        A dict mapping each section name to its extracted content.
    """
    # Build a PromptTemplate that injects both system_prompt and the resume text.
    #    We ask the model to respond in strict JSON.

    system_prompt = (
        """
    As a specialized resume parsing AI, your objective is to deconstruct submitted resumes and organize their content into the following standardized sections:

    - **Name**
    - **Contact Information**: (e.g., Phone, Email Address, Address)
    - **Education**: (e.g., School Name, Degree, Dates, GPA)
    - **Work Experience**: (e.g., Job Title, Company, Dates, Responsibilities)
    - **Skills**: (e.g., Soft Skills, Tech Skills)
    - **Projects**: (e.g., Project Name, Description, Technologies Used, Dates)
    - **Achievements & Hackathons**: (e.g., Awards, Recognition)

    Extract all relevant data for each section. **If a section has no content, omit that section entirely from the JSON output.** Your output must be a single JSON object, containing nothing else. Do not include any introductory or explanatory text.
        """
    )

    template = """\
    System: {system_prompt}

    Resume Text:
    \"\"\"
    {text}
    \"\"\"

    Please output a JSON object representing the parsed resume data.
    """

    prompt = PromptTemplate(
        input_variables=["system_prompt", "text"],
        template=template
    )

    llm = OllamaLLM(
        base_url="http://localhost:11434",  # or wherever your Ollama server lives
        model=model_name,
        timeout=300,
    )

    # Create the chain and run it
    chain = prompt | llm
    raw_output = chain.invoke({
        "system_prompt": system_prompt,
        "text": text,
    })

    return raw_output

def main():
    # --- Configuration ---
    PDF_PATH = r"resume_layout_2.pdf" <- File CV dưới định dạng PDF
    OUTPUT_IMG_DIR = "pages_img"
    OCR_OUTPUT_DIR = "ocr_text"
    DPI = 300  # increase for better OCR accuracy

    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    os.makedirs(OCR_OUTPUT_DIR, exist_ok=True)


    convert_pdf_to_img(PDF_PATH, dpi=DPI, img_dir=OUTPUT_IMG_DIR)
    ocr_output = applyOCR(OUTPUT_IMG_DIR, OCR_OUTPUT_DIR)

    processed_text = text_processing(ocr_output)

    parsed_output = extract_resume_sections(
        text=processed_text,
        model_name="llama3.2",
    )

    print(parsed_output)

    res = ast.literal_eval(parsed_output)
    print(type(res), res)
  ## Chưa hoàn chỉnh


if __name__ == '__main__':
    main()
