<template>
  <div class="container">
    <!-- 左側：解析結果與檔案區域 -->
    <div class="left-panel">
      <h1>NCC OCR 文件解析平台</h1>
      <input type="file" @change="uploadFiles" multiple />
      <p>解析結果：</p>
      <textarea v-model="ocrResult" rows="10" cols="80"></textarea>

      <div class="file-section">
        <h3>Select Files</h3>
        <ul class="select-file-list">
          <li v-for="file in files" :key="file">
            <label>
              <input
                type="radio"
                :value="file"
                :checked="selectedFile === file"
                @click="toggleSelection(file)"
              />
              <a
                :href="`${baseURL}/download/${encodeURIComponent(file)}`"
                target="_blank"
              >
                {{ file }}
              </a>
            </label>
            <button @click="confirmDelete(file)" class="delete-button">
              ✖
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 右側：聊天室 -->
    <div class="chat-wrapper">
      <h2 class="chat-title">Chat</h2>
      <div class="chat-container" ref="chatContainer">
        <div
          v-for="(msg, index) in chatMessages"
          :key="index"
          class="chat-message"
          :class="{
            'user-msg': msg.role === 'user',
            'bot-msg': msg.role === 'assistant',
          }"
        >
          <strong>{{ msg.role === "user" ? "使用者" : "NCC 助手" }}:</strong>
          {{ msg.content }}
        </div>
      </div>

      <div class="chat-input">
        <textarea
          v-model="userQuery"
          @keydown.enter.prevent="askQuestion"
        ></textarea>
        <button @click="askQuestion">Send</button>
      </div>
    </div>

    <!-- Loading 遮罩 -->
    <div v-if="isUploading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>檔案上傳中，請稍候...</p>
    </div>
  </div>
</template>

<script>
import {
  fetchFiles,
  askQuestion,
  handleFileUpload,
  uploadFileForOCR,
  deleteFile,
} from "./methods.js";

export default {
  data() {
    return {
      baseURL: "http://127.0.0.1:8000",
      userQuery: "",
      selectedFile: "",
      chatMessages: [], // 確保這裡初始化 chatMessages
      uploadedFileName: "",
      uploadedFiles: [],
      files: [],
      ocrResult: "", // 初始化為空字符串
      isUploading: false, // 控制是否顯示 Loading 畫面
    };
  },
  mounted() {
    this.fetchFiles(this);
  },
  methods: {
    fetchFiles() {
      fetchFiles(this);
    },

    updateFilesList() {
      this.files = [...this.uploadedFiles]; // 更新 files 數組
    },
    toggleSelection(file) {
      if (this.selectedFile === file) {
        this.selectedFile = null; // 取消選擇
      } else {
        this.selectedFile = file; // 選擇新文件
      }
    },

    askQuestion() {
      if (!this.userQuery.trim()) {
        console.error("請輸入問題");
        return;
      }
      const question = this.userQuery;
      const fileName = this.selectedFile; // 使用選擇的文件名
      console.log("Selected file:", fileName); // 確認選擇的文件名
      askQuestion(this, question, fileName);
      this.userQuery = ""; // 清空輸入框
    },

    handleFileUploadWrapper(event) {
      handleFileUpload(this, event);
    },

    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file.name; // 設置選擇的文件名
        this.uploadedFileName = file.name; // 設置上傳的文件名
        console.log("文件已選擇:", this.selectedFile);
      }
    },

    async uploadFiles(event) {
      const files = event.target.files;
      if (!files.length) return;

      this.isUploading = true; // 顯示 Loading 畫面
      this.uploadedFiles = [];
      this.ocrResult = "";

      for (let i = 0; i < files.length; i++) {
        const result = await uploadFileForOCR(this, files[i]);
        if (
          result &&
          result.results &&
          result.results[0] &&
          result.results[0].text
        ) {
          this.uploadedFiles.push(files[i].name);
          this.ocrResult += `文件 ${files[i].name} 的結果:\n${result.results[0].text}\n\n`;
        } else {
          console.error(`Failed to process file: ${files[i].name}`);
        }
      }

      this.isUploading = false; // 隱藏 Loading 畫面
      alert("所有文件上傳成功！");
      this.fetchFiles();
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const chatContainer = this.$refs.chatContainer;
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      });
    },
    async deleteFile(file) {
      await deleteFile(this, file);
    },
    confirmDelete(file) {
      const confirmed = confirm("確定要刪除嗎？");
      if (confirmed) {
        this.deleteFile(file);
      }
    },
  },
};
</script>

<style>
/* 主要容器，使用 Flexbox 讓左右區域佔 60% / 40% */
.container {
  display: flex;
  height: 100vh; /* 讓整個畫面填滿 */
}

/* 左側區域（解析結果 + 檔案區域） */
.left-panel {
  flex: 3; /* 佔 60% */
  padding: 20px;
  overflow-y: auto;
  background: #f4f4f9;
  display: flex;
  flex-direction: column;
}

/* 檔案列表區塊 */
.file-section {
  margin-top: 20px;
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

/* 檔案列表 */
.file-list {
  min-height: 150px; /* 設定最小高度，確保區塊不會塌陷 */
  max-height: 300px; /* 設定最大高度，超過時啟用滾動 */
  overflow-y: auto; /* 當內容超過 max-height 時顯示滾動條 */
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px;
  background: #fafafa;
}

/* 檔案列表 */
ul {
  list-style: none;
  padding: 0;
}

li {
  background: #fff;
  padding: 10px;
  margin: 5px 0;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

li:hover {
  background: #f0f0f0;
}

/* 刪除按鈕 */
.delete-button {
  background: none;
  border: none;
  color: black;
  cursor: pointer;
  font-size: 0.8em;
}

.delete-button:hover {
  color: #555;
}

/* 右側區域（聊天室） */
.chat-wrapper {
  flex: 2; /* 佔 40% */
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: white;
  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
  padding: 15px;
}

/* 聊天室標題 */
.chat-title {
  text-align: center;
  padding: 10px;
  font-size: 20px;
  font-weight: bold;
  background: #f4f4f4; /* 恢復原本的淺灰色背景 */
  color: #333; /* 深灰色文字 */
  border-radius: 8px;
  margin-bottom: 10px;
}

/* 讓聊天區域可以滾動 */
.chat-container {
  flex: 1;
  border: 1px solid #ddd;
  padding: 15px;
  overflow-y: auto;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.1);
}

/* 訊息樣式 */
.chat-message {
  padding: 10px 15px;
  border-radius: 20px;
  margin: 8px 0;
  max-width: 75%;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.3s ease-in-out;
}

/* 使用者訊息（靠右） */
.user-msg {
  align-self: flex-end;
  background: #d1e7dd; /* 恢復原本的綠色背景 */
  color: #333;
  text-align: right;
}

/* 機器人訊息（靠左） */
.bot-msg {
  align-self: flex-start;
  background: #f8d7da; /* 恢復原本的粉紅色背景 */
  color: #333;
}

/* 輸入區 */
.chat-input {
  display: flex;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
}

/* 輸入框 */
.chat-input textarea {
  flex: 1;
  height: 50px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  transition: border 0.3s ease-in-out;
}

.chat-input textarea:focus {
  border-color: #999;
  outline: none;
}

/* 送出按鈕 */
.chat-input button {
  margin-left: 10px;
  padding: 10px 15px;
  background: #666; /* 恢復原本的深灰色 */
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 8px;
  font-size: 14px;
  transition: background 0.3s ease-in-out;
}

.chat-input button:hover {
  background: #444;
}

/* 訊息淡入動畫 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 響應式設計：在小螢幕上改為上下排列 */
@media (max-width: 768px) {
  .container {
    flex-direction: column;
  }

  .left-panel,
  .chat-wrapper {
    flex: none;
    width: 100%;
    height: 50vh;
  }
}

/* Loading 遮罩 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  z-index: 1000;
}

/* Loading 旋轉動畫 */
.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-top: 5px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 解析結果標題 */
p {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

/* 解析結果輸入框 */
textarea {
  width: 97%;
  height: 300px; /* 增加高度 */
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px; /* 圓角 */
  background: #fafafa; /* 淺灰色背景 */
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.1); /* 內陰影 */
  transition: border 0.3s ease-in-out, background 0.3s ease-in-out;
}

textarea:focus {
  border-color: #666;
  background: white;
  outline: none;
}

/* 讓 "Select Files" 也有滾動條 */
.select-file-list {
  min-height: 150px; /* 設定最小高度，確保區塊不會塌陷 */
  max-height: 300px; /* 設定最大高度，超過時啟用滾動 */
  overflow-y: auto; /* 當內容超過 max-height 時顯示滾動條 */
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px;
  background: #fafafa;
}
</style>
