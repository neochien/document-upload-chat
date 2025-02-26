const BASE_URL = "http://localhost:8000"; // Docker Compose 內部網路名稱

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

export async function uploadFileForOCR(context, file) {
  const formData = new FormData();
  formData.append("files", file);

  try {
    const response = await fetch(`${context.baseURL}/upload/`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }

    const result = await response.json();
    console.log("Server response:", result); // 在控制台查看服务器返回的响应
    if (!result.results || !result.results[0] || !result.results[0].text) {
      console.error("OCR result missing 'text' property");
    } else {
      console.log("OCR text:", result.results[0].text); // 确保正确解析 text 属性
    }
    return result; // 确保返回结果对象
  } catch (error) {
    console.error("Error uploading file:", error);
    return { text: "Error processing file" }; // 返回一个默认的错误结果
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
