<template>
  <div>
    <h1>NCC OCR 文件解析平台</h1>
    <input type="file" @change="uploadFile" />
    <p>解析結果：</p>
    <textarea v-model="ocrResult" rows="10" cols="80"></textarea>
  </div>

  <div id="app">
    <h3>Uploaded Files</h3>
    <ul>
      <li v-for="file in files" :key="file">
        <a
          :href="`${baseURL}/download/${encodeURIComponent(file)}`"
          target="_blank"
        >
          {{ file }}
        </a>
      </li>
    </ul>

    <h3>Select Files</h3>
    <ul>
      <li v-for="file in files" :key="file">
        <label>
          <input
            type="radio"
            :value="file"
            :checked="selectedFile === file"
            @click="toggleSelection(file)"
          />
          {{ file }}
        </label>
        <button @click="confirmDelete(file)" class="delete-button">✖</button>
      </li>
    </ul>

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
      ocrResult: "",
    };
  },
  mounted() {
    this.fetchFiles(this);
  },
  methods: {
    fetchFiles() {
      fetchFiles(this);
    },
    async uploadFileForOCR(event) {
      await uploadFileForOCR(this, event);
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

    async uploadFile(event) {
      await uploadFileForOCR(this, event);
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
/* 聊天區域包裹容器 */
.chat-wrapper {
  width: 50%; /* 將寬度設置為 50% */
  position: fixed; /* 使用固定定位 */
  right: 0; /* 放置在右邊 */
  top: 0; /* 從頂部開始 */
  height: 100%; /* 佔滿右半邊的高度 */
  display: flex;
  flex-direction: column;
  box-sizing: border-box; /* 確保 padding 不影響寬度 */
}

/* 聊天室標題 */
.chat-title {
  text-align: center;
  padding: 5px;
  background-color: #f1f1f1;
  border-bottom: 1px solid #ddd;
}

/* 讓聊天區域可以滾動 */
.chat-container {
  flex: 1; /* 讓聊天區域佔滿剩餘空間 */
  border: 1px solid #ddd;
  padding: 10px;
  overflow-y: auto;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
}

/* 訊息樣式 */
.chat-message {
  padding: 8px;
  border-radius: 10px;
  margin: 5px 0;
  max-width: 80%;
}

/* 使用者訊息（靠右） */
.user-msg {
  align-self: flex-end;
  background: #d1e7dd;
}

/* 機器人訊息（靠左） */
.bot-msg {
  align-self: flex-start;
  background: #f8d7da;
}

/* 輸入區 */
.chat-input {
  display: flex;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

.chat-input textarea {
  flex: 1;
  height: 50px;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 5px;
  resize: none;
}

.chat-input button {
  margin-left: 10px;
  padding: 5px 10px;
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.delete-button {
  background: none;
  border: none;
  color: #000000; /* 黑色 */
  cursor: pointer;
  font-size: 1em; /* 字体大小 */
  margin-left: 5px; /* 左边距 */
  padding: 0;
}

.delete-button:hover {
  color: #555555; /* 悬停时的颜色 */
}
</style>
