# MatrixQuesGen Client

Frontend React cho hệ thống sinh câu hỏi tự động.

## Tech Stack

- React 18
- Vite
- Tailwind CSS
- React Router
- Axios

## Development

### Install dependencies

```bash
npm install
```

### Run development server

```bash
npm run dev
```

App sẽ chạy tại: http://localhost:3000

API proxy tự động chuyển requests `/api/*` tới `http://localhost:8000`

### Build for production

```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── layout/          # AppLayout, Header, Sidebar
│   └── generate/        # Matrix input, Preview panels
├── pages/               # Route pages
├── services/            # API clients
├── App.jsx
└── main.jsx
```

## Features

### 1. Sinh đề (Generate Exam)

- Upload file Excel ma trận
- Cấu hình tham số sinh (workers, retries...)
- Preview câu hỏi real-time
- Export DOCX

### 2. Quản lý (Manage Exams)

- Danh sách đề đã sinh
- Xem chi tiết
- Export lại
- Xóa

### 3. Ma trận đề (Matrix Library)

- Coming soon

## Design Principles

- Internal tool aesthetic (không phải marketing site)
- Clean, functional UI
- Tham khảo: Google AI Studio, Cloud Console
- Không gradient, không animation phô trương
- Focus vào productivity

## API Integration

Tất cả API calls được centralize trong `src/services/api.js`

Example:

```javascript
import { generateQuestions, getGenerationProgress } from "./services/api";

// Upload và sinh
const result = await generateQuestions(file, {
  max_workers: 5,
  max_retries: 3,
});

// Check progress
const progress = await getGenerationProgress(result.session_id);
```
