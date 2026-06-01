# 流程圖文件 (Flowchart)

> **說明**：由於專案中目前尚未建立 `docs/PRD.md` 與 `docs/ARCHITECTURE.md`，以下流程圖與架構是基於「Heart-Check（心臟健康管理系統）」的標準情境進行設計。系統主要提供使用者記錄心跳、血壓等健康數據，並支援完整的 CRUD（新增、讀取、更新、刪除）操作。

## 1. 使用者流程圖（User Flow）

描述使用者進入網站後，與系統互動的主要操作路徑。

```mermaid
flowchart LR
  A([使用者開啟網頁]) --> B[首頁 - 健康紀錄列表]
  B --> C{要執行什麼操作？}
  C -->|新增| D[填寫新增紀錄表單]
  C -->|查看| E[查看單筆紀錄詳細資訊]
  C -->|編輯| F[填寫編輯紀錄表單]
  C -->|刪除| G[確認刪除對話框]
  
  D -->|送出表單| H([儲存成功，返回首頁])
  F -->|送出表單| H
  G -->|確認| I([刪除成功，返回首頁])
  E -->|返回| B
```

## 2. 系統序列圖（Sequence Diagram）

描述「使用者點擊新增」到「資料存入資料庫」的完整技術流程。

```mermaid
sequenceDiagram
  actor User as 使用者
  participant Browser as 使用者瀏覽器
  participant Flask as Flask Route
  participant Model as Model (資料模型)
  participant DB as SQLite 資料庫
  
  User->>Browser: 填寫心臟健康紀錄表單並點擊送出
  Browser->>Flask: POST /records (包含表單資料)
  Flask->>Model: 驗證資料並建立 Record 實例
  Model->>DB: INSERT INTO records (心跳、收縮壓、舒張壓等)
  DB-->>Model: 回傳成功狀態與新紀錄 ID
  Model-->>Flask: 回傳建立成功
  Flask-->>Browser: HTTP 302 重導向到列表頁 (GET /)
  Browser-->>User: 顯示新增成功訊息與最新紀錄列表
```

## 3. 功能清單對照表

列出系統主要功能、對應的 URL 路徑與 HTTP 方法。

| 功能名稱 | URL 路徑 | HTTP 方法 | 說明 |
| :--- | :--- | :--- | :--- |
| **首頁 / 紀錄列表** | `/` 或 `/records` | `GET` | 顯示所有心臟健康紀錄的列表 |
| **顯示新增表單** | `/records/new` | `GET` | 顯示用於新增紀錄的 HTML 表單頁面 |
| **處理新增紀錄** | `/records` | `POST` | 接收表單資料，寫入資料庫並重導向至列表頁 |
| **查看單筆紀錄** | `/records/<id>` | `GET` | 顯示特定 ID 的紀錄詳細資訊 |
| **顯示編輯表單** | `/records/<id>/edit` | `GET` | 顯示用於編輯紀錄的 HTML 表單頁面，並帶入現有資料 |
| **處理編輯紀錄** | `/records/<id>/edit` | `POST` | 接收編輯後的表單資料，更新資料庫並重導向至列表頁 |
| **處理刪除紀錄** | `/records/<id>/delete`| `POST` | 刪除特定 ID 的紀錄，並重導向至列表頁 |
