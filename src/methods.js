const BASE_URL = "http://127.0.0.1:8000"; // 定義基礎 URL

export async function fetchFiles(vm) {
  try {
    const response = await fetch(`${BASE_URL}/files`); // 請求 FastAPI 的 /files API
    const data = await response.json();

    if (data.files) {
      vm.files = data.files; // 更新 Vue 的 files 陣列
    }
  } catch (error) {
    console.error("Failed to fetch files:", error);
  }
}

export async function handleFileUpload(vm, event) {
  const formData = new FormData();
  formData.append("file", event.target.files[0]);

  try {
    const response = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.filename) {
      console.log("File uploaded successfully:", data.filename);
      fetchFiles(vm);
      vm.uploadedFileName = data.filename;
    } else {
      console.error("Upload failed:", data);
    }
  } catch (error) {
    console.error("Failed to upload file:", error);
  }
}

export function scrollToBottom(vm) {
  vm.$nextTick(() => {
    const chatContainer = vm.$refs.chatContainer;
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
}

export async function uploadFileForOCR(vm, event) {
  const formData = new FormData();
  formData.append("file", event.target.files[0]);

  try {
    const response = await fetch(`${BASE_URL}/upload/`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.filename) {
      console.log("OCR 解析結果:", data.text);
      vm.ocrResult = data.text; // 儲存 OCR 結果
      vm.uploadedFileName = data.filename; // 儲存上傳檔案名稱
      console.log("已儲存檔案名稱:", vm.uploadedFileName); // 確認檔案名稱是否更新
      vm.fetchFiles(); // 確保檔案列表是最新的
      alert("文件上傳成功");
    } else {
      console.error("OCR 解析失敗:", data);
    }
  } catch (error) {
    console.error("OCR API 呼叫失敗:", error);
  }
}

export async function askQuestion(vm, question, fileName) {
  if (!question.trim()) {
    console.error("請輸入問題");
    return;
  }

  console.log(
    "sending question:",
    question,
    "for file:",
    fileName || "未指定文件"
  );

  // 先把用戶輸入的問題加入對話框
  vm.chatMessages.push({ role: "user", content: question });

  try {
    const response = await fetch(`${BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        file_name: fileName || null, // 確保傳送檔案名稱，若無則為 null
      }),
    });

    const data = await response.json();
    if (data.answer) {
      console.log("Answer:", data.answer);

      // 加入機器人回應
      vm.chatMessages.push({ role: "assistant", content: data.answer });

      // 強制 Vue 重新渲染
      vm.chatMessages = [...vm.chatMessages];

      // 確保滾動到最新訊息
      vm.$nextTick(() => {
        vm.scrollToBottom();
      });
    } else {
      console.error("後端回應錯誤:", data.error);
    }
  } catch (error) {
    console.error("API 呼叫失敗:", error);
  }
}

export async function deleteFile(vm, file) {
  try {
    const response = await fetch(
      `${BASE_URL}/delete/${encodeURIComponent(file)}`,
      {
        method: "DELETE",
      }
    );

    if (response.ok) {
      vm.files = vm.files.filter((f) => f !== file);
      if (vm.selectedFile === file) {
        vm.selectedFile = ""; // 如果刪除的是選中的文件，清空選擇
      }
      console.log(`文件 ${file} 已刪除`);
    } else {
      const errorData = await response.json();
      console.error(`刪除文件 ${file} 失敗: ${errorData.detail}`);
    }
  } catch (error) {
    console.error("API 呼叫失敗:", error);
  }
}
