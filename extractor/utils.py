import fitz

import pandas as pd

import docx

from PIL import Image

import pytesseract

def extract_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    return text

def extract_docx(path):

    document = docx.Document(path)

    return "\n".join(
        para.text
        for para in document.paragraphs
    )

def extract_txt(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()
    
def extract_excel(path):

    workbook = pd.ExcelFile(path)

    content = []

    for sheet in workbook.sheet_names:

        dataframe = pd.read_excel(
            path,
            sheet_name=sheet
        )

        content.append(
            dataframe.to_string()
        )

    return "\n".join(content)

def extract_image(path):

    image = Image.open(path)

    return pytesseract.image_to_string(
        image
    )

def extract_text(path):

    path = path.lower()

    if path.endswith(".pdf"):
        return extract_pdf(path)

    if path.endswith(".docx"):
        return extract_docx(path)

    if path.endswith(".txt"):
        return extract_txt(path)

    if path.endswith(
        (".xlsx", ".xls")
    ):
        return extract_excel(path)

    if path.endswith(
        (".jpg",".jpeg",".png")
    ):
        return extract_image(path)

    return "Unsupported file type"