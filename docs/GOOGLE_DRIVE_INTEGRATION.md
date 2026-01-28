# Google Drive API Integration

## Tổng quan

Module này cung cấp khả năng tải xuống files từ Google Drive thông qua API.

## Cài đặt

### 1. Dependencies

Đã thêm vào `server-requirements.txt`:

- `google-api-python-client==2.110.0`
- `google-auth-httplib2==0.1.1`
- `google-auth-oauthlib==1.2.0`

### 2. Service Account Credentials

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo hoặc chọn project
3. Kích hoạt Google Drive API
4. Tạo Service Account và tải xuống JSON key file
5. Đặt file credentials vào thư mục an toàn (không commit vào git)

### 3. Cấu hình Environment

Thêm vào file `.env`:

```env
GOOGLE_DRIVE_CREDENTIALS_PATH=path/to/your/service-account.json
```

## API Endpoints

### 1. Download File

**POST** `/google-drive/download`

Tải xuống file từ Google Drive.

**Request Body:**

```json
{
  "file_id": "1abc...xyz",
  "file_name": "optional_filename.pdf"
}
```

**Response:** File binary

### 2. Get File Info

**GET** `/google-drive/file-info/{file_id}`

Lấy thông tin metadata của file.

**Response:**

```json
{
  "id": "1abc...xyz",
  "name": "document.pdf",
  "mimeType": "application/pdf",
  "size": "12345",
  "modifiedTime": "2024-01-01T00:00:00.000Z"
}
```

### 3. List Folder Files

**POST** `/google-drive/list-folder`

Liệt kê files trong folder.

**Request Body:**

```json
{
  "folder_id": "1def...uvw",
  "query": "mimeType='application/pdf'" // optional
}
```

**Response:**

```json
{
  "success": true,
  "files": [
    {
      "id": "1abc...xyz",
      "name": "file1.pdf",
      "mimeType": "application/pdf",
      "size": "12345"
    }
  ]
}
```

## Sử dụng trong Frontend

```javascript
// Download file
const downloadFile = async (fileId, fileName) => {
  const response = await fetch("/google-drive/download", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      file_id: fileId,
      file_name: fileName,
    }),
  });

  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName || "downloaded_file";
    a.click();
  }
};

// Get file info
const getFileInfo = async (fileId) => {
  const response = await fetch(`/google-drive/file-info/${fileId}`);
  const data = await response.json();
  console.log(data);
};
```

## Lưu ý Bảo mật

- Service Account chỉ có quyền read-only theo mặc định
- Không share credentials file
- Validate file_id inputs để tránh path traversal
- Files tạm thời được xóa tự động sau khi download

## Troubleshooting

1. **Authentication failed**: Kiểm tra đường dẫn credentials file
2. **Access denied**: Đảm bảo Service Account có quyền truy cập file/folder
3. **File not found**: Kiểm tra file_id có chính xác không
4. **Quota exceeded**: Google Drive API có rate limits
