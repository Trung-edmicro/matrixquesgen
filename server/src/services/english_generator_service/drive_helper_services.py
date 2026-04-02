import logging
from pathlib import Path
import re
logger = logging.getLogger(__name__)
import requests
from services.solute_exam_service.solute_english_exam_service import API_KEY
import os
import sys

DRIVE_VOCABULARY_FOLDER_C10 = "https://drive.google.com/drive/folders/18tVQXctKZdpj8ZrFJhA0cU-xpLBj5Du2"

DRIVE_VOCABULARY_FOLDER_C11 = "https://drive.google.com/drive/folders/1FqzI2Y-zIWUMnDNCrFCc_Yw-yR0Pm8PT"

DRIVE_VOCABULARY_FOLDER_C12 = "https://drive.google.com/drive/folders/16Ke0JMipcJbHMIWEWiV1rQh234Mei0pV"

DRIVE_FOLDER = "https://drive.google.com/drive/folders/1JSFC8FBTY6lA0rlrC7-LAIHU_FjbOK3g"

# ==================== APP_DIR Detection ====================
def _get_app_dir():
    """
    Lấy APP_DIR từ environment variable hoặc tính toán từ file path.
    Dev: __file__.parent.parent.parent.parent.parent
    Build exe: từ APP_DIR env var
    """
    app_dir = os.environ.get('APP_DIR')
    if app_dir:
        return Path(app_dir)
    
    # Dev mode: tính từ file path hiện tại
    # server/src/services/english_generator_service/drive_helper_services.py
    # -> parent.parent.parent.parent.parent = matrixquesgen/
    current_file = Path(os.path.dirname(os.path.abspath(__file__)))
    return current_file.parent.parent.parent.parent

APP_DIR = _get_app_dir()
LOCAL_VOCAB_DIR = APP_DIR / "data" / "vocabulary_english"
LOCAL_PROMPT_DIR = APP_DIR / "data" / "prompts" / "prompts_english"

# Ensure directories exist
LOCAL_VOCAB_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_PROMPT_DIR.mkdir(parents=True, exist_ok=True)

drive_prompts_cache = None



def get_local_file_path(topic):
    filename = f"{topic.strip().lower()}.txt"
    return LOCAL_VOCAB_DIR / filename


def read_local_file(topic):
    path = get_local_file_path(topic)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_local_file(topic, content):
    path = get_local_file_path(topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def fetch_drive_txt_files(folder_url):
    """
    Lấy tất cả file .txt trong 1 Google Drive folder
    return dict {filename: content}
    """
    try:
        folder_id = re.search(r"folders/([a-zA-Z0-9_-]+)", folder_url).group(1)

        url = f"https://drive.google.com/drive/folders/{folder_id}"
        html_text = requests.get(url).text

        file_ids = list(set(re.findall(r'"([a-zA-Z0-9_-]{25,})"', html_text)))

        txt_files = {}

        for fid in file_ids:
            download_url = f"https://drive.google.com/uc?export=download&id={fid}"
            r = requests.get(download_url)

            if r.status_code != 200:
                continue

            disposition = r.headers.get("content-disposition", "")

            if ".txt" not in disposition:
                continue

            name_match = re.findall(r'filename="(.+)"', disposition)

            if not name_match:
                continue

            filename = name_match[0]
            txt_files[filename] = r.text

        return txt_files

    except Exception as e:
        logger.warning(f"Cannot fetch vocabulary from drive: {e}")
        return {}

def sync_drive_to_local():
    """
    Đồng bộ toàn bộ file txt từ Google Drive về local
    """

    print("🔄 Syncing vocabulary from Google Drive...")

    folders = [
        DRIVE_VOCABULARY_FOLDER_C10,
        DRIVE_VOCABULARY_FOLDER_C11,
        DRIVE_VOCABULARY_FOLDER_C12
    ]

    all_drive_files = {}

    # 1. Lấy toàn bộ file từ Drive
    for folder_url in folders:
        folder_id = re.search(r"folders/([a-zA-Z0-9_-]+)", folder_url).group(1)

        files = fetch_drive_txt_files(folder_id)

        for filename, content in files.items():
            all_drive_files[filename.strip()] = content

    # 2. So sánh + update local
    for filename, drive_content in all_drive_files.items():
        local_path = LOCAL_VOCAB_DIR / filename

        # Nếu file chưa tồn tại → tạo mới
        if not local_path.exists():
            print(f"🆕 Creating: {filename}")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(drive_content)
            continue

        # Nếu tồn tại → so sánh nội dung
        with open(local_path, "r", encoding="utf-8") as f:
            local_content = f.read()

        if local_content.strip() != drive_content.strip():
            print(f"♻️ Updating: {filename}")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(drive_content)
        else:
            print(f"✅ No change: {filename}")

    print("✅ Sync completed.")


def load_vocabulary_local(topic):
    """
    Load vocabulary từ file local (KHÔNG gọi API nữa)
    """

    if not topic:
        return ""

    topic_clean = topic.strip().lower()

    if not LOCAL_VOCAB_DIR.exists():
        return ""

    for file_item in LOCAL_VOCAB_DIR.iterdir():
        if not file_item.is_file() or not file_item.suffix == ".txt":
            continue

        name = file_item.stem.strip().lower()

        if name == topic_clean:
            with open(file_item, "r", encoding="utf-8") as f:
                return f.read()

    return ""

_drive_vocab_cache = None


# def load_vocabulary_from_drive(topic):
#     """
#     Tìm file txt có tên trùng topic trong 3 folder drive
#     """
#     global _drive_vocab_cache

#     # ✅ Handle None / NaN / non-string
#     if topic is None:
#         print("⚠️ Topic is None")
#         return ""

#     # convert sang string nếu không phải string
#     if not isinstance(topic, str):
#         topic = str(topic)

#     topic_clean = topic.strip().lower()

#     if not topic_clean:
#         print("⚠️ Topic is empty")
#         return ""

#     if _drive_vocab_cache is None:

#         print("🔎 Fetching vocabulary from Drive folders...")

#         folders = [
#             DRIVE_VOCABULARY_FOLDER_C10,
#             DRIVE_VOCABULARY_FOLDER_C11,
#             DRIVE_VOCABULARY_FOLDER_C12
#         ]

#         vocab_data = {}

#         for folder in folders:
#             files = fetch_drive_txt_files(folder)
#             vocab_data.update(files)

#         _drive_vocab_cache = vocab_data

#     for filename, content in _drive_vocab_cache.items():

#         name = filename.replace(".txt", "").strip().lower()

#         if name == topic_clean:
#             print(f"✅ Vocabulary loaded from Drive: {filename}")
#             print(f">>>>> debug content {content}")
#             return content

#     return ""

def list_files_in_folder(folder_id):
    """
    Lấy danh sách file trong folder bằng Google Drive API
    """
    url = "https://www.googleapis.com/drive/v3/files"

    params = {
        "key": API_KEY,
        "q": f"'{folder_id}' in parents and trashed=false",
        "fields": "files(id, name, mimeType)"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        logger.error("❌ Cannot list files from Drive")
        return []

    return response.json().get("files", [])


def download_file(file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={API_KEY}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    try:
        return response.content.decode("utf-8")
    except UnicodeDecodeError:
        return response.content.decode("utf-8", errors="ignore")


def fetch_drive_txt_files(folder_id):
    """
    Lấy tất cả file .txt trong 1 folder
    """

    try:
        url = "https://www.googleapis.com/drive/v3/files"

        params = {
            "key": API_KEY,
            "q": f"'{folder_id}' in parents and name contains '.txt' and trashed=false",
            "fields": "files(id, name)"
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.error("❌ Cannot list files from Drive")
            return {}

        files = response.json().get("files", [])

        txt_files = {}

        for f in files:
            content = download_file(f["id"])

            if content is None:
                continue

            txt_files[f["name"]] = content

        return txt_files

    except Exception as e:
        logger.error(f"❌ Error fetching txt files: {e}")
        return {}

def load_vocabulary_from_drive(topic):
    """
    Tìm file txt theo topic trong 3 folder Drive (không dùng cache)
    """

    if topic is None:
        print("⚠️ Topic is None")
        return ""

    if not isinstance(topic, str):
        topic = str(topic)

    topic_clean = topic.strip().lower()

    if not topic_clean:
        print("⚠️ Topic is empty")
        return ""

    print("🔎 Fetching vocabulary from Drive API...")

    folders = [
        DRIVE_VOCABULARY_FOLDER_C10,
        DRIVE_VOCABULARY_FOLDER_C11,
        DRIVE_VOCABULARY_FOLDER_C12
    ]

    for folder_url in folders:
        folder_id = re.search(r"folders/([a-zA-Z0-9_-]+)", folder_url).group(1)

        files = fetch_drive_txt_files(folder_id)

        for filename, content in files.items():
            name = filename.replace(".txt", "").strip().lower()

            if name == topic_clean:
                print(f"✅ Found: {filename}")
                return content

    return ""

