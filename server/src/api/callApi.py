# # api/callApi.py
import os
import sys
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models._generative_models import _GenerativeModel, Part, GenerationConfig
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions
from google.oauth2 import service_account
from google.genai import types
from pathlib import Path

EMBEDDED_CREDS = ""
# if getattr(sys, 'frozen', False):
#     base_path = sys._MEIPASS
# else:
#     base_path = os.path.dirname(__file__)
 
# dotenv_path = os.path.join(base_path, '.env')
# load_dotenv(dotenv_path)
 
if getattr(sys, "frozen", False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).resolve().parents[3]  # lùi 3 cấp

dotenv_path = base_path / ".env"
load_dotenv(dotenv_path)


def _safe_get_env(key, required=True):
    """Lấy biến môi trường an toàn. Nếu required True và không tồn tại -> raise error rõ ràng."""
    val = os.getenv(key)
    print(f">>>>>> debug val {val}")
    if required and (val is None or val == ""):
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return val

def get_vertex_ai_credentials():
    """
    Hàm helper để lấy credentials, dùng chung cho cả callAPI và text2Image.
    """
    try:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            print("❌ [API] Lỗi: Không tìm thấy PRIVATE_KEY trong .env")
            return None

        service_account_data = {
            "type": os.getenv("TYPE"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": private_key.replace('\\n', '\n'),
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN")
        }
        
        creds = service_account.Credentials.from_service_account_info(
            service_account_data,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return creds
    except Exception as e:
        print(f"❌ [API] Lỗi khi tạo credentials: {e}")
        return None
 
def _normalize_private_key(pk_raw):
    """Bảo vệ việc gọi replace trên None và chuyển các escape '\\n' thành newline thật."""
    if pk_raw is None:
        return None
    # Nếu key đã là multiline (ví dụ khi chạy local), trả về nguyên bản
    if "\\n" in pk_raw:
        return pk_raw.replace("\\n", "\n")
    return pk_raw
 
 
def _validate_service_account_dict(d):
    """Đảm bảo service account dict có các trường cần thiết."""
    required_keys = ["type", "project_id", "private_key", "client_email"]
    missing = [k for k in required_keys if not d.get(k)]
    if missing:
        raise EnvironmentError(f"Service account JSON thiếu trường: {missing}")
 
 
def get_credentials():
    """
    Load Google Cloud credentials.
    - Nếu EMBEDDED_CREDS khác rỗng -> dùng JSON nhúng (dùng cho .exe build).
    - Ngược lại -> đọc từ các biến môi trường / .env (dùng local).
    Trả về: (google.oauth2.service_account.Credentials, project_id)
    """
    try:
        # 1) Nếu có credential nhúng -> parse JSON
        if EMBEDDED_CREDS and EMBEDDED_CREDS.strip():
            try:
                service_account_data = json.loads(EMBEDDED_CREDS)
            except Exception as e:
                raise EnvironmentError(f"EMBEDDED_CREDS không hợp lệ: {e}")
 
            # Normalize private_key nếu cần
            if "private_key" in service_account_data:
                service_account_data["private_key"] = _normalize_private_key(service_account_data["private_key"])
 
            _validate_service_account_dict(service_account_data)
            project_id = service_account_data.get("project_id")
        else:
            # 2) Fallback: đọc từ environment / .env
            # Lấy private_key raw (cẩn trọng: có thể là multiline hoặc escaped)
            private_key_raw = os.getenv("PRIVATE_KEY")
            private_key = _normalize_private_key(private_key_raw)
 
            # Thu thập các giá trị (required = True đối với các trường quan trọng)
            service_account_data = {
                "type": _safe_get_env("TYPE"),
                "project_id": _safe_get_env("PROJECT_ID"),
                "private_key_id": os.getenv("PRIVATE_KEY_ID", ""),
                "private_key": private_key,
                "client_email": _safe_get_env("CLIENT_EMAIL"),
                "client_id": os.getenv("CLIENT_ID", ""),
                "auth_uri": os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL", ""),
                "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL", ""),
                "universe_domain": os.getenv("UNIVERSE_DOMAIN", "")
             
 
            }
 
            print(f"Loaded service account for project: {service_account_data.get('project_id')}")
 
            _validate_service_account_dict(service_account_data)
            project_id = service_account_data.get("project_id")
 
        # Tạo credentials object
        credentials = service_account.Credentials.from_service_account_info(
            service_account_data,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
 
        return credentials, project_id
 
    except Exception as e:
        # Bọc lỗi, trả về message rõ ràng cho caller
        raise Exception(f"Không thể load credentials: {e}")
 
 
# ---------------- Vertex client class (giữ nguyên logic của bạn, tối ưu chút) ----------------
class VertexClient:
    def __init__(self, project_id, creds, model, region="us-central1"):
        vertexai.init(
            project=project_id,
            location=region,
            credentials=creds
        )
        self.model = _GenerativeModel(model)
 
    # def send_data_to_AI(self, prompt, file_paths=None, temperature=0.5, top_p=0.8):
    #     print(f">>>>>> debug prompt {prompt}")
    #     parts = []
    #     if file_paths:
    #         for file_path in file_paths:
    #             with open(file_path, "rb") as f:
    #                 pdf_bytes = f.read()
    #             parts.append(Part.from_data(data=pdf_bytes, mime_type="application/pdf"))
 
    #     parts.append(Part.from_text(prompt))
 
    #     generation_config = GenerationConfig(
    #         temperature=temperature,
    #         top_p=top_p,
    #         max_output_tokens=12000,
    #         candidate_count=1
    #     )
 
    #     response = self.model.generate_content(parts, generation_config=generation_config)

    #     print(f">>>>>>> debu response {response.text}")

    #     return response.text


    def send_multiple_data_to_AI(self, prompt, file_paths=None, temperature=0.2, top_p=0.1):
        print(f">>>>>> debug prompt length: {len(prompt)} chars")
        parts = []
        
        if file_paths:
            for file_path in file_paths:
                try:
                    ext = os.path.splitext(file_path)[1].lower()
                    # Xác định mime_type dựa trên đuôi file
                    if ext == '.pdf':
                        mime_type = "application/pdf"
                    elif ext == '.docx':
                        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    else:
                        print(f"⚠️ Định dạng file không hỗ trợ, bỏ qua: {file_path}")
                        continue

                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    
                    if len(file_bytes) == 0:
                        raise ValueError(f"File rỗng: {file_path}")
                    
                    parts.append(Part.from_data(data=file_bytes, mime_type=mime_type))
                    print(f"  - Đã tải file: {os.path.basename(file_path)} ({mime_type})")
                except Exception as e:
                    print(f">>>>>> ERROR reading file {file_path}: {e}")
                    raise

        parts.append(Part.from_text(prompt))

        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=65355,
            candidate_count=1
        )

        try:
            print(">>>>>> Sending request to Vertex AI...")
            response = self.model.generate_content(parts, generation_config=generation_config)

            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                full_text = "".join(
                    part.text for part in candidate.content.parts
                    if hasattr(part, 'text') and part.text is not None
                )
            else:
                full_text = response.text if response.text else ""
            
            return full_text
        except Exception as e:
            print(f">>>>>> ERROR: {type(e).__name__}: {e}")
            raise


    def send_data_to_AI(self, prompt, file_paths=None, temperature=0.0, top_p=0.1):
        print(f">>>>>> debug prompt length: {len(prompt)} chars")
        if file_paths:
            total_size = sum(os.path.getsize(f) for f in file_paths)
            print(f">>>>>> total PDF size: {total_size / (1024*1024):.2f} MB")
            for i, fp in enumerate(file_paths):
                print(f"  - File {i+1}: {os.path.basename(fp)} ({os.path.getsize(fp) / (1024*1024):.2f} MB)")

        parts = []
        if file_paths:
            for file_path in file_paths:
                try:
                    with open(file_path, "rb") as f:
                        pdf_bytes = f.read()
                    # Kiểm tra file không rỗng
                    if len(pdf_bytes) == 0:
                        raise ValueError(f"File PDF rỗng: {file_path}")
                    parts.append(Part.from_data(data=pdf_bytes, mime_type="application/pdf"))
                except Exception as e:
                    print(f">>>>>> ERROR reading PDF {file_path}: {e}")
                    raise

        parts.append(Part.from_text(prompt))

        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=65355,
            candidate_count=1,
            # media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
        )

        try:
            # print(">>>>>> Sending request to Vertex AI...")
            # response = self.model.generate_content(parts, generation_config=generation_config)
            # print(f">>>>>> Received response successfully response. {response}")
            # print(f">>>>>> Received response successfully. {response.text}")
            # return response.text
                print(">>>>>> Sending request to Vertex AI...")
                response = self.model.generate_content(parts, generation_config=generation_config)

                # 🔧 LẤY TEXT ĐÚNG CÁCH: HỖ TRỢ MULTI-PART ✅
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    # Ghép tất cả part có .text lại
                    full_text = "".join(
                        part.text for part in candidate.content.parts
                        if hasattr(part, 'text') and part.text is not None
                    )
                else:
                    # Fallback nếu không có parts (lý thuyết không xảy ra)
                    full_text = response.text if response.text else ""
                print(f">>>>> full text {full_text}")
                # print(f">>>>>> Received response successfully. Text length: {len(full_text)} chars")
                return full_text
        except google_exceptions.InvalidArgument as e:
            print(f">>>>>> INVALID ARGUMENT ERROR (400): {e}")
            print(f"Details: {e.details if hasattr(e, 'details') else 'No details'}")
            raise
        except google_exceptions.BadRequest as e:
            print(f">>>>>> BAD REQUEST (400): {e}")
            raise
        except Exception as e:
            print(f">>>>>> OTHER ERROR: {type(e).__name__}: {e}")
            raise

    def send_data_md_to_AI(self, prompt, file_paths=None, temperature=0.2, top_p=0.8):
        print(f">>>>>> debug prompt length: {len(prompt)} chars")
        
        parts = []
        if file_paths:
            total_size = sum(os.path.getsize(f) for f in file_paths)
            print(f">>>>>> total Markdown size: {total_size / 1024:.2f} KB")
            
            for i, fp in enumerate(file_paths):
                try:
                    # Kiểm tra extension để đảm bảo là file md
                    if not fp.lower().endswith('.md'):
                        print(f"  - Warning: File {fp} does not have .md extension")

                    with open(fp, "rb") as f:
                        md_bytes = f.read()
                    
                    if len(md_bytes) == 0:
                        print(f"  - Warning: File MD rỗng: {fp}")
                        continue
                    
                    # Sử dụng mime_type="text/markdown" cho file .md
                    # Nếu model báo lỗi type, có thể dùng "text/plain"
                    parts.append(Part.from_data(data=md_bytes, mime_type="text/markdown"))
                    print(f"  - File {i+1}: {os.path.basename(fp)} loaded.")
                    
                except Exception as e:
                    print(f">>>>>> ERROR reading MD {fp}: {e}")
                    raise

        # Thêm prompt text vào cuối
        parts.append(Part.from_text(prompt))

        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=65355,
            candidate_count=1
        )

        try:
            print(">>>>>> Sending request to Vertex AI (Markdown Mode)...")
            response = self.model.generate_content(parts, generation_config=generation_config)
            
            # Cách lấy text an toàn hơn (tránh lỗi nếu response bị chặn bởi safety filters)
            try:
                if response.candidates and response.candidates[0].content.parts:
                    full_text = "".join(part.text for part in response.candidates[0].content.parts if part.text)
                    print(f">>>>>> Received response successfully. Length: {len(full_text)}")
                    return full_text
                else:
                    print(">>>>>> No text content found in response (might be blocked).")
                    return ""
            except (AttributeError, IndexError, ValueError) as e:
                # Fallback nếu response.text có sẵn nhưng cấu trúc phức tạp
                print(f">>>>>> Error parsing response text: {e}")
                return response.text if hasattr(response, 'text') else ""

        except google_exceptions.InvalidArgument as e:
            print(f">>>>>> INVALID ARGUMENT ERROR (400): {e}")
            raise
        except google_exceptions.BadRequest as e:
            print(f">>>>>> BAD REQUEST (400): {e}")
            raise
        except Exception as e:
            print(f">>>>>> OTHER ERROR: {type(e).__name__}: {e}")
            raise
        
 
    def send_data_to_check(self, prompt, temperature=0.2, top_p=0.8):
        parts = [Part.from_text(prompt)]
        generation_config = GenerationConfig(temperature=temperature, top_p=top_p)
        response = self.model.generate_content(parts, generation_config=generation_config)
        return response.text
 


