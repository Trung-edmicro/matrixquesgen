import logging
import re
logger = logging.getLogger(__name__)
import requests



DRIVE_VOCABULARY_FOLDER_C10 = "https://drive.google.com/drive/folders/18tVQXctKZdpj8ZrFJhA0cU-xpLBj5Du2"

DRIVE_VOCABULARY_FOLDER_C11 = "https://drive.google.com/drive/folders/1FqzI2Y-zIWUMnDNCrFCc_Yw-yR0Pm8PT"

DRIVE_VOCABULARY_FOLDER_C12 = "https://drive.google.com/drive/folders/16Ke0JMipcJbHMIWEWiV1rQh234Mei0pV"

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



_drive_vocab_cache = None

# def load_vocabulary_from_drive(topic):
#     """
#     Tìm file txt có tên trùng topic trong 3 folder drive
#     """
#     global _drive_vocab_cache

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

#     topic_clean = topic.strip().lower()

#     for filename, content in _drive_vocab_cache.items():

#         name = filename.replace(".txt", "").strip().lower()

#         if name == topic_clean:
#             print(f"✅ Vocabulary loaded from Drive: {filename}")
#             return content

#     return ""

def load_vocabulary_from_drive(topic):
    """
    Tìm file txt có tên trùng topic trong 3 folder drive
    """
    global _drive_vocab_cache

    # ✅ Handle None / NaN / non-string
    if topic is None:
        print("⚠️ Topic is None")
        return ""

    # convert sang string nếu không phải string
    if not isinstance(topic, str):
        topic = str(topic)

    topic_clean = topic.strip().lower()

    if not topic_clean:
        print("⚠️ Topic is empty")
        return ""

    if _drive_vocab_cache is None:

        print("🔎 Fetching vocabulary from Drive folders...")

        folders = [
            DRIVE_VOCABULARY_FOLDER_C10,
            DRIVE_VOCABULARY_FOLDER_C11,
            DRIVE_VOCABULARY_FOLDER_C12
        ]

        vocab_data = {}

        for folder in folders:
            files = fetch_drive_txt_files(folder)
            vocab_data.update(files)

        _drive_vocab_cache = vocab_data

    for filename, content in _drive_vocab_cache.items():

        name = filename.replace(".txt", "").strip().lower()

        if name == topic_clean:
            print(f"✅ Vocabulary loaded from Drive: {filename}")
            return content

    return ""