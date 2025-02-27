import os
import time
import subprocess
from pdf2image import convert_from_path
import pytesseract
from docx2pdf import convert
from PIL import Image
from docx import Document

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang="chi_tra+eng+chi_sim", config='--oem 3 --psm 6')

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    return "\n".join(pytesseract.image_to_string(image, lang="chi_tra+eng+chi_sim", config='--oem 3 --psm 6') for image in images)

def extract_text_from_docx_with_ocr(docx_path):
    pdf_path = docx_path.replace('.docx', '.pdf')
    
    try:
        # 使用 LibreOffice 進行 DOCX → PDF 轉換
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", os.path.dirname(docx_path), docx_path
        ], check=True)

        text = extract_text_from_pdf(pdf_path)

        # 清理轉換的 PDF 文件
        os.remove(pdf_path)
        return text

    except subprocess.CalledProcessError as e:
        print(f"Error converting {docx_path} to PDF: {e}")
        return ""
    except Exception as e:
        print(f"Error processing {docx_path}: {e}")
        return ""

def process_file(file_path):
    """處理單個檔案，回傳 OCR 結果"""
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx_with_ocr(file_path)
    elif file_path.endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_path)
    else:
        return None
