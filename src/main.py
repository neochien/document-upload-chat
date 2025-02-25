import os
import shutil
import time
import pdfplumber
import pytesseract
import openai
from pdf2image import convert_from_path
from docx import Document
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from typing import List
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
from ocr_utils import process_file
import json


app = FastAPI()

# 設定 CORS 策略
origins = [
    "http://192.168.10.155:8080",  # 允許這個來源
    "http://127.0.0.1:8080",       # 允許本地開發端口
    "http://localhost:8080",        # 允許本地開發端口
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許的來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許的 HTTP 方法
    allow_headers=["*"],  # 允許的標頭
)



UPLOAD_DIR = "uploads"
OCR_DATA_DIR = "ocr_data"

# 確保資料夾存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OCR_DATA_DIR, exist_ok=True)

# OpenAI API Key
# openai.api_key = "sk-crossbot-Ng1ub6lMlFJAW6aW7wB9T3BlbkFJqwsWkMe7ocCghoyTbLFn"
# client = openai.OpenAI(api_key=os.getenv("sk-crossbot-Ng1ub6lMlFJAW6aW7wB9T3BlbkFJqwsWkMe7ocCghoyTbLFn"))
client = openai.OpenAI(api_key="sk-crossbot-Ng1ub6lMlFJAW6aW7wB9T3BlbkFJqwsWkMe7ocCghoyTbLFn")

custom_config = r'--oem 3 --psm 6'

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/files")
async def list_files():
    """ 列出上傳的檔案，排除 `.DS_Store` """
    try:
        files = [
            f for f in os.listdir(UPLOAD_DIR)
            if f != ".DS_Store" and os.path.isfile(os.path.join(UPLOAD_DIR, f)) 
        ]
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}  # 如果資料夾不存在，返回空列表
    

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    json_path = os.path.join(OCR_DATA_DIR, f"{filename}.json")

    # 刪除文件
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        return {"error": "File not found."}

    # 刪除對應的 JSON 文件
    if os.path.exists(json_path):
        os.remove(json_path)
    else:
        return {"error": "OCR data not found."}

    return {"message": f"File {filename} and its OCR data have been deleted."}


OCR_DATA={}

# 1. 上傳文件
def save_ocr_data(filename, data):
    json_path = os.path.join(OCR_DATA_DIR, f"{filename}.json")
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



@app.post("/upload/")
async def upload_and_process_files(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # 存檔案
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR 處理
        extracted_text = process_file(file_path)
        print(f"Extracted text for {file.filename}: {extracted_text}")  # 增加日志记录

        # 移除檔案 (可選，避免佔用磁碟空間)
        # os.remove(file_path)

        # 保存 OCR 結果到單獨的 JSON 文件
        save_ocr_data(file.filename, {"text": extracted_text})

        results.append({"filename": file.filename, "text": extracted_text})

    print(f"Returning results: {results}")  # 增加日志记录
    return {"results": results}




# 2. 處理目錄中的所有文件
@app.get("/process_files")
def process_files():
    all_results = {}

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)

        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif filename.endswith(".docx"):
            text = extract_text_from_word(file_path)
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            text = extract_text_from_image(file_path)
        else:
            continue  # 忽略不支援的文件類型

        # 送入 OpenAI 進行問答
        answer = send_file_to_openai(filename, text)
        all_results[filename] = answer

    return {"results": all_results}

from fastapi.responses import FileResponse

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}



# 3. 問答接口
# @app.post("/ask")
# async def ask_question(request: Request):
#     try:
#         # 取得使用者提出的問題
#         data = await request.json()
#         user_question = data.get("question")
        
#         # 呼叫處理文件並傳給 OpenAI 的邏輯
#         result = process_files()  # 這裡需要傳遞 filename 和 text
#         return {"answer": result}  # 回傳 OpenAI 的回答
#     except Exception as e:
#         # 如果發生錯誤，返回錯誤訊息
#         return {"error": str(e)}

def load_ocr_data_from_file(file_name):
    json_path = os.path.join(OCR_DATA_DIR, f"{file_name}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return None

@app.post("/ask")
async def ask_question(request: Request):
    try:
        # 取得使用者問題
        data = await request.json()
        user_question = data.get("question")
        file_name = data.get("file_name")

        if not user_question:
            return {"error": "Question is required."}

        # 如果提供了文件名，從 JSON 文件中讀取數據
        if file_name:
            ocr_data = load_ocr_data_from_file(file_name)
            if ocr_data is None:
                return {"error": "File not found."}
            extracted_text = ocr_data.get("text", "無法讀取文本內容。")
        else:
            # 如果沒有提供文件名，使用默認文本或空文本
            extracted_text = "沒有提供文件，使用默認文本。"

        # 這裡輸出收到的資料，幫助確認是否正確處理
        print(f"Received question: {user_question} for file: {file_name or '未指定文件'}")
        print(f"Extracted text: {extracted_text}")

        # 發送問題到 OpenAI
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",  # 你可以換成 gpt-4
            messages=[
                {"role": "system", "content": (
                    "你是NCC國家通訊委員會的助手，請根據提供的文件內容回答問題。"
                    "當使用者跟你親切地打招呼的時候，請你介紹自己的回應他。"
                    "如果使用者提到「整理重點」，請整理出以下資訊，並在每個屬性之間換行：\n"
                    # "1. 設備名稱：\n"
                    # "2. 廠牌：\n"
                    # "3. 型號：\n"
                    # "4. 頻率：\n"
                    # "5. 功率：\n\n"
                    "1. 廠牌：\n"
                    "2. 型號：\n"
                    "3. 頻率：\n"
                    "4. 功率：\n\n"
                    "請確保信息準確，並保留原始單位，若無該資訊，請回覆「無」。"
                    "若使用者有特定之需求，請依照他的需求輸出資訊。"
                    "將簡體中文轉成繁體中文，並在每個設備之間用空行分隔。"
                )},
                {"role": "user", "content": f"文件名：{file_name or '未指定文件'}\n以下是文件內容：\n{extracted_text}\n\n請回答以下問題：\n{user_question}"},
            ],
        )

        # 取得回應的內容
        answer = response.choices[0].message.content
        return {"answer": answer}

    except Exception as e:
        return {"error": str(e)}

# ========== OCR & OpenAI 相關函數 ==========

def extract_text_from_pdf(file_path: str):
    images = convert_from_path(file_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang="chi_tra+eng+chi_sim", config=custom_config)
    return text


def extract_text_from_word(file_path: str):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def extract_text_from_image(file_path: str):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang="chi_tra+eng+chi_sim", config=custom_config)
    return text


def send_file_to_openai(filename, text):
    # 定義要發送的訊息，包含系統訊息和使用者問題
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": text}  # 這裡的 `text` 是使用者的問題
    ]
    
    # 發送請求並獲得回應
    response = openai.chat_completions.create(
        model="gpt-4o-latest",  # 替換為你想要的模型，例如 gpt-4
        messages=messages
    )
    
    # 回傳回答的內容
    return response['choices'][0]['message']['content']


def send_query_to_openai(query, context):
    """ 發送使用者的問題給 OpenAI，並提供 OCR 內容作為背景 """
    response = openai.ChatCompletion.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": ""},
            {"role": "user", "content": f"文件內容:\n{context}\n\n問題: {query}"}
        ]
    )
    return response['choices'][0]['message']['content']

def process_files():
    # 這裡假設你會先解析文件，並將解析的文字傳給 OpenAI
    # 假設 `filename` 是檔案名稱，`text` 是從檔案中提取的內容
    answer = send_file_to_openai(filename, text)  # 傳遞檔案和問題給 OpenAI
    return answer