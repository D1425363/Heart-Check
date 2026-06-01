# API 路由設計文件 (docs/ROUTES.md)

本文件定義「Heart Check 校園互助與人氣回饋平台」的所有 Flask 路由規格、處理邏輯與 Jinja2 模板對照。

---

## 1. 路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| **[註冊頁面]** 顯示註冊表單 | GET | `/register` | `templates/auth/register.html` | 顯示使用者註冊表單 |
| **[註冊帳號]** 建立新使用者 | POST | `/register` | — (重導向 `/login`) | 接收表單欄位，在資料庫建立新使用者 |
| **[登入頁面]** 顯示登入表單 | GET | `/login` | `templates/auth/login.html` | 顯示使用者登入表單 |
| **[登入驗證]** 驗證憑證並建立會話 | POST | `/login` | — (重導向 `/profile` 或 `/`) | 驗證密碼與帳號，成功後寫入 session |
| **[登出]** 清除會話 | GET | `/logout` | — (重導向 `/login`) | 移除 session 中使用者資訊並登出 |
| **[個人檔案]** 顯示愛心、人氣與 QR Code | GET | `/profile` | `templates/user/profile.html` | 顯示當前使用者的愛心值、累積人氣值與歷史交易 |
| **[掃描 QR Code]** 顯示轉移頁面 | GET | `/qr/<token>` | `templates/user/qr_transfer.html` | 顯示給予特定幫助者愛心值與留言的表單頁面 |
| **[愛心值轉移]** 執行交易扣除/增加愛心 | POST | `/qr/<token>/transfer`| — (重導向 `/profile`) | 扣除發送者愛心，增加接收者人氣，寫入交易紀錄 |
| **[排行榜]** 顯示愛心與人氣排行 | GET | `/leaderboard` | `templates/user/leaderboard.html` | 顯示人氣值最高的前 10 名使用者 |
| **[失物招領列表]** 顯示並篩選公告 | GET | `/items` | `templates/item/list.html` | 顯示所有尋物/拾獲公告，支援關鍵字與狀態篩選 |
| **[新增失物招領頁面]** 顯示新增表單 | GET | `/items/new` | `templates/item/new.html` | 提供發布遺失/拾獲物品公告的填寫表單 |
| **[建立失物招領]** 儲存物品資料與上傳圖片 | POST | `/items/new` | — (重導向 `/items`) | 接收表單與上傳照片，寫入失物招領資料庫 |
| **[失物招領詳情]** 顯示單筆詳細資訊 | GET | `/items/<int:item_id>` | `templates/item/detail.html` | 顯示指定物品的詳細資訊與聯絡方式 |
| **[編輯失物招領頁面]** 顯示編輯表單 | GET | `/items/<int:item_id>/edit`| `templates/item/edit.html` | 載入現有物品資訊並顯示編輯表單 |
| **[更新失物招領]** 更新物品資訊 | POST | `/items/<int:item_id>/update`| — (重導向 `/items/<item_id>`) | 接收表單並更新失物招領資料庫 |
| **[刪除失物招領]** 刪除公告 | POST | `/items/<int:item_id>/delete`| — (重導向 `/items`) | 刪除該筆失物招領資料並移除實體相片 |
| **[標記為已認領/尋回]** 變更物品狀態 | POST | `/items/<int:item_id>/claim` | — (重導向 `/items/<item_id>`) | 將物品狀態設為已認領 (claimed) |
| **[平台首頁]** 首頁大廳 | GET | `/` | `templates/board/home.html` | 整合顯示最新公告、最新失物招領與使用者簡介 |
| **[公告列表]** 顯示公告清單 | GET | `/announcements` | `templates/board/announcements.html` | 顯示校園與宿舍公告，支援按分類篩選 |
| **[新增公告頁面]** 顯示公告表單 | GET | `/announcements/new`| `templates/board/announcement_new.html` | 管理者新增公告填寫表單 (限幹部/管理員) |
| **[建立公告]** 儲存公告內容 | POST | `/announcements/new`| — (重導向 `/announcements`) | 接收表單並儲存至公告資料庫 |
| **[編輯公告頁面]** 顯示編輯公告表單 | GET | `/announcements/<int:announcement_id>/edit`| `templates/board/announcement_edit.html` | 載入公告現有內容並顯示編輯表單 |
| **[更新公告]** 更新公告內容 | POST | `/announcements/<int:announcement_id>/update`| — (重導向 `/announcements`) | 接收表單並更新公告資料庫 |
| **[刪除公告]** 刪除該筆公告 | POST | `/announcements/<int:announcement_id>/delete`| — (重導向 `/announcements`) | 刪除公告資料庫中的指定公告紀錄 |
| **[交通資訊]** 顯示校區交通資訊 | GET | `/info/traffic` | `templates/board/traffic.html` | 顯示校車時刻表與校園通勤資訊 |
| **[餐廳資訊]** 顯示校區餐廳評價 | GET | `/info/restaurants` | `templates/board/restaurants.html` | 顯示學生餐廳與周邊餐廳資訊與基本評價 |

---

## 2. 每個路由的詳細說明

### 2.1 認證模組 (Auth - `app/routes/auth.py`)

#### `GET /register`
* **輸入**：無
* **處理邏輯**：
  1. 渲染註冊頁面。
  2. 若使用者已登入（Session 中有 `user_id`），直接重導向至個人檔案頁面 `/profile`。
* **輸出**：渲染 `auth/register.html`
* **錯誤處理**：無

#### `POST /register`
* **輸入**：表單欄位：`username` (必填), `password` (必填), `name` (必填), `student_id` (必填), `department` (選填)
* **處理邏輯**：
  1. 驗證欄位是否填寫完整。
  2. 呼叫 `User.get_by_username(username)` 與自訂 SQL 檢查 `student_id` 是否在資料庫中已存在 (需保持唯一)。
  3. 將密碼使用安全雜湊演算法（如 bcrypt）處理。
  4. 產生專屬且唯一的安全隨機 `qr_code_token` (透過 `secrets.token_hex(16)`)。
  5. 呼叫 `User.create(username, password_hash, name, student_id, department, qr_code_token=qr_code_token)` 寫入 `users` 資料表，預設愛心餘額 (`heart_balance`) 為 100，人氣值 (`popularity`) 為 0。
  6. 註冊成功後，引導至登入頁面並使用 Flask Flash 顯示成功訊息。
* **輸出**：重導向至 `/login`
* **錯誤處理**：
  - 欄位缺失：重新渲染 `auth/register.html` 並帶入錯誤訊息與保留已填欄位。
  - 帳號或學號重複：回傳錯誤提示「該帳號或學號已被註冊」，重新渲染註冊表單。

#### `GET /login`
* **輸入**：無
* **處理邏輯**：渲染登入頁面。若使用者已登入，直接重導向至 `/profile`。
* **輸出**：渲染 `auth/login.html`
* **錯誤處理**：無

#### `POST /login`
* **輸入**：表單欄位：`username` (必填), `password` (必填)
* **處理邏輯**：
  1. 呼叫 `User.get_by_username(username)` 查詢使用者資料。
  2. 比對輸入密碼與資料庫中的 `password_hash`。
  3. 若比對成功，將該使用者的 `id` 寫入 Flask `session['user_id']` 中，完成登入。
* **輸出**：重導向至個人檔案頁面 `/profile`
* **錯誤處理**：
  - 帳號不存在或密碼錯誤：重新渲染 `auth/login.html` 並使用 Flash 顯示「帳號或密碼錯誤」訊息。

#### `GET /logout`
* **輸入**：無
* **處理邏輯**：清除 Flask `session` 中的 `user_id` 與所有登入資訊。
* **輸出**：重導向至 `/login`
* **錯誤處理**：無

---

### 2.2 使用者與愛心模組 (User - `app/routes/user.py`)

#### `GET /profile`
* **輸入**：Session 中需存有 `user_id` (需登入驗證)
* **處理邏輯**：
  1. 根據 `session['user_id']` 呼叫 `User.get_by_id(user_id)` 查詢使用者資料。
  2. 獲取 `heart_balance`、`popularity` 與 `qr_code_token`。
  3. 呼叫 `HeartTransaction.get_by_user_id(user_id)` 查詢與此使用者相關的所有愛心交易歷史紀錄（包含發出與收到）。
  4. 渲染個人檔案頁面，並透過前端或 API 根據 `qr_code_token` 生成專屬 QR Code。
* **輸出**：渲染 `user/profile.html`
* **錯誤處理**：
  - 未登入：重導向至 `/login` 並提示需登入。
  - 使用者不存在：清除 session 並重導向至 `/login`。

#### `GET /qr/<token>`
* **輸入**：URL 參數 `token` (幫助者的 `qr_code_token`)，需登入驗證
* **處理邏輯**：
  1. 呼叫 `User.get_by_qr_code_token(token)` 尋找對應的接收者（幫助者）。
  2. 確保接收者不是目前登入的使用者自己（不能發送愛心給自己）。
  3. 載入接收者的名稱，顯示給予愛心值的操作頁面。
* **輸出**：渲染 `user/qr_transfer.html`
* **錯誤處理**：
  - 無效的 Token / 找不到接收者：回傳 404 頁面，提示「此 QR Code 無效」。
  - 發送給自己：重導向至 `/profile` 並提示「無法對自己進行愛心轉移」。

#### `POST /qr/<token>/transfer`
* **輸入**：URL 參數 `token`；表單欄位：`heart_amount` (必填), `thank_you_message` (選填)
* **處理邏輯**：
  1. 呼叫 `User.get_by_qr_code_token(token)` 取得接收者 ID（幫助者）。
  2. 驗證當前登入者（發送者）的 `heart_balance` 是否大於等於 `heart_amount`。
  3. 驗證 `heart_amount` 必須大於 0。
  4. 呼叫 `HeartTransaction.transfer_hearts(sender_id, receiver_id, heart_amount, thank_you_message)`，在資料庫交易 (Transaction) 中：
     - 發送者的 `heart_balance` 減去 `heart_amount`，並呼叫 `user.update()`。
     - 接收者的 `popularity` 加上 `heart_amount`，並呼叫 `user.update()`。
     - 寫入 `heart_transactions` 資料表紀錄。
  5. 交易成功後，設定 Flash 成功訊息「成功發送愛心與感謝！」。
* **輸出**：重導向至 `/profile`
* **錯誤處理**：
  - 餘額不足：渲染 `user/qr_transfer.html` 並顯示「愛心值餘額不足」。
  - 數量小於等於 0：顯示「發送數量必須大於 0」。
  - 資料庫寫入失敗：自動 Rollback，顯示「交易失敗，請稍後再試」。

#### `GET /leaderboard`
* **輸入**：無
* **處理邏輯**：
  1. 呼叫 `User.get_top_by_popularity(limit=10)` 查詢人氣值最高的前 10 名使用者。
* **輸出**：渲染 `user/leaderboard.html`
* **錯誤處理**：無

---

### 2.3 失物招領模組 (Item - `app/routes/item.py`)

#### `GET /items`
* **輸入**：Query Parameters (選填)：`type` (lost/found), `status` (unclaimed/claimed), `q` (關鍵字)
* **處理邏輯**：
  1. 呼叫 `Item.get_all()` 或 `Item.get_by_type(item_type)` 獲取物品。
  2. 根據 `status` 與 `q` 在 Python 層或 SQL 層進行條件過濾。
  3. 排序依 `created_at` 由新到舊。
* **輸出**：渲染 `item/list.html`
* **錯誤處理**：無

#### `GET /items/new`
* **輸入**：需登入驗證
* **處理邏輯**：確認已登入後，渲染新增物品公告的表單頁面。
* **輸出**：渲染 `item/new.html`
* **錯誤處理**：
  - 未登入：重導向至 `/login`。

#### `POST /items/new`
* **輸入**：表單欄位：`title` (必填), `description` (必填), `location` (必填), `item_type` (lost/found, 必填), `contact_info` (選填)；檔案欄位：`image` (選填)
* **處理邏輯**：
  1. 驗證必填欄位。
  2. 若使用者有上傳圖片，驗證副檔名並儲存到 `app/static/images/`，取得相對路徑 `image_url`。
  3. 呼叫 `Item.create(title, description, location, item_type, status='unclaimed', user_id=session['user_id'], image_url=image_url, contact_info=contact_info)` 寫入資料庫。
* **輸出**：重導向至 `/items`
* **錯誤處理**：
  - 欄位缺失：重新渲染 `item/new.html` 並顯示錯誤提示「請填寫所有必填欄位」。

#### `GET /items/<int:item_id>`
* **輸入**：URL 參數 `item_id`
* **處理邏輯**：
  1. 呼叫 `Item.get_by_id(item_id)` 取得指定物品詳細資料。
* **輸出**：渲染 `item/detail.html`
* **錯誤處理**：
  - 找不到物品：回傳 404 頁面，提示「此物品公告不存在或已被刪除」。

#### `GET /items/<int:item_id>/edit`
* **輸入**：URL 參數 `item_id`，需登入驗證
* **處理邏輯**：
  1. 呼叫 `Item.get_by_id(item_id)` 取得物品資料。
  2. 驗證當前登入者是否為該物品的發布者 (`item.user_id == session['user_id']`)。
* **輸出**：渲染 `item/edit.html` 並帶入既有資料
* **錯誤處理**：
  - 未登入：重導向至 `/login`。
  - 非作者本人編輯：回傳 403 拒絕存取，或重導向至詳情頁並顯示警告。

#### `POST /items/<int:item_id>/update`
* **輸入**：URL 參數 `item_id`；表單欄位同建立物品，外加 `status` (unclaimed/claimed)；檔案欄位：`image` (選填)
* **處理邏輯**：
  1. 呼叫 `Item.get_by_id(item_id)` 取得物品資料並驗證修改權限。
  2. 接收修改表單欄位。若有上傳新圖片，刪除舊圖片並儲存新圖。
  3. 更新物件屬性，並呼叫 `item.update()` 寫入資料庫。
* **輸出**：重導向至 `/items/<item_id>`
* **錯誤處理**：
  - 權限不足：回傳 403 拒絕。
  - 資料庫更新失敗：顯示系統錯誤。

#### `POST /items/<int:item_id>/delete`
* **輸入**：URL 參數 `item_id`，需登入驗證
* **處理邏輯**：
  1. 呼叫 `Item.get_by_id(item_id)` 取得物品資料並驗證刪除權限。
  2. 呼叫 `item.delete()` 自資料庫刪除記錄，並在檔案系統刪除關聯圖片。
* **輸出**：重導向至 `/items`
* **錯誤處理**：
  - 權限不足：回傳 403 拒絕。

#### `POST /items/<int:item_id>/claim`
* **輸入**：URL 參數 `item_id`，需登入驗證
* **處理邏輯**：
  1. 呼叫 `Item.get_by_id(item_id)` 取得物品資料並驗證修改權限。
  2. 將 `item.status` 屬性修改為 `'claimed'`，並呼叫 `item.update()` 儲存。
* **輸出**：重導向至 `/items/<item_id>`
* **錯誤處理**：
  - 權限不足：回傳 403 拒絕。

---

### 2.4 公告與資訊模組 (Board - `app/routes/board.py`)

#### `GET /` (首頁)
* **輸入**：無
* **處理邏輯**：
  1. 呼叫 `Announcement.get_all()`，取出最新的 3 筆公告。
  2. 呼叫 `Item.get_all()`，篩選取出最新的 3 筆協尋中（`status == 'unclaimed'`）物品。
  3. 若已登入，呼叫 `User.get_by_id(session['user_id'])` 取得當前使用者簡短資料（展示於 Header）。
* **輸出**：渲染 `board/home.html`
* **錯誤處理**：無

#### `GET /announcements`
* **輸入**：Query Parameters (選填)：`category` (dorm/campus)
* **處理邏輯**：
  1. 若有 `category`，呼叫 `Announcement.get_by_category(category)` 獲取特定公告。
  2. 若無篩選，呼叫 `Announcement.get_all()` 獲取全部公告。
* **輸出**：渲染 `board/announcements.html`
* **錯誤處理**：無

#### `GET /announcements/new`
* **輸入**：需登入驗證，且使用者必須為幹部/管理員
* **處理邏輯**：
  1. 驗證登入狀態。
  2. 檢查使用者權限（例如：資料庫中 `users` 表的特定權限，或此處示範的宿舍幹部身份核對）。
  3. 渲染建立公告的表單。
* **輸出**：渲染 `board/announcement_new.html`
* **錯誤處理**：
  - 未登入或權限不足：回傳 403 拒絕存取，或重導向至 `/announcements` 並顯示警告。

#### `POST /announcements/new`
* **輸入**：表單欄位：`title` (必填), `content` (必填), `category` (dorm/campus, 必填)
* **處理邏輯**：
  1. 驗證權限。
  2. 驗證欄位完整度。
  3. 呼叫 `Announcement.create(title, content, category, author_id=session['user_id'])` 儲存至資料庫。
* **輸出**：重導向至 `/announcements`
* **錯誤處理**：
  - 欄位缺失：重新渲染並提示錯誤。

#### `GET /announcements/<int:announcement_id>/edit`
* **輸入**：URL 參數 `announcement_id`，需登入驗證且限作者/管理員編輯
* **處理邏輯**：
  1. 呼叫 `Announcement.get_by_id(announcement_id)` 取得公告內容。
  2. 檢查當前登入者是否具有編輯權限 (`announcement.author_id == session['user_id']` 或高級管理者)。
* **輸出**：渲染 `board/announcement_edit.html`
* **錯誤處理**：
  - 公告不存在：回傳 404。
  - 權限不足：回傳 403。

#### `POST /announcements/<int:announcement_id>/update`
* **輸入**：URL 參數 `announcement_id`；表單欄位：`title` (必填), `content` (必填), `category` (必填)
* **處理邏輯**：
  1. 呼叫 `Announcement.get_by_id(announcement_id)` 驗證修改權限。
  2. 更新公告的 `title`、`content`、`category` 屬性。
  3. 呼叫 `announcement.update()` 將修改儲存回資料庫。
* **輸出**：重導向至 `/announcements`
* **錯誤處理**：
  - 權限不足：回傳 403。

#### `POST /announcements/<int:announcement_id>/delete`
* **輸入**：URL 參數 `announcement_id`，需登入驗證
* **處理邏輯**：
  1. 呼叫 `Announcement.get_by_id(announcement_id)` 驗證刪除權限。
  2. 呼叫 `announcement.delete()` 從資料庫刪除該筆公告。
* **輸出**：重導向至 `/announcements`
* **錯誤處理**：
  - 權限不足：回傳 403。

#### `GET /info/traffic`
* **輸入**：無
* **處理邏輯**：直接載入靜態/動態校園校車與捷運動態交通資訊。
* **輸出**：渲染 `board/traffic.html`
* **錯誤處理**：無

#### `GET /info/restaurants`
* **輸入**：無
* **處理邏輯**：載入學區餐廳列表與預設評價資料。
* **輸出**：渲染 `board/restaurants.html`
* **錯誤處理**：無

---

## 3. Jinja2 模板清單與繼承關係

全站模板均繼承 `templates/base.html`，以保持統一的 UI 外觀與 Header/Footer 樣式。

* **基礎框架模板**：
  * `templates/base.html`：定義網頁主骨架、導覽列（含登入狀態切換）、Footer，並留有 `{% block content %}` 與 `{% block styles %}` 區塊供子頁面填入。
  
* **Auth (認證頁面)**：
  * `templates/auth/register.html`：註冊表單，繼承自 `base.html`
  * `templates/auth/login.html`：登入表單，繼承自 `base.html`

* **User (個人/互動頁面)**：
  * `templates/user/profile.html`：個人檔案與 QR Code，繼承自 `base.html`
  * `templates/user/qr_transfer.html`：愛心值留言發送頁，繼承自 `base.html`
  * `templates/user/leaderboard.html`：排行榜展示，繼承自 `base.html`

* **Item (失物招領)**：
  * `templates/item/list.html`：失物招領總覽，繼承自 `base.html`
  * `templates/item/new.html`：新增尋物/拾獲表單，繼承自 `base.html`
  * `templates/item/detail.html`：物件詳情與聯絡資訊，繼承自 `base.html`
  * `templates/item/edit.html`：編輯表單，繼承自 `base.html`

* **Board (公告看板與靜態資訊)**：
  * `templates/board/home.html`：首頁大廳，繼承自 `base.html`
  * `templates/board/announcements.html`：公告清單，繼承自 `base.html`
  * `templates/board/announcement_new.html`：新增公告，繼承自 `base.html`
  * `templates/board/announcement_edit.html`：編輯公告，繼承自 `base.html`
  * `templates/board/traffic.html`：校園交通時刻，繼承自 `base.html`
  * `templates/board/restaurants.html`：學餐餐廳評價，繼承自 `base.html`
