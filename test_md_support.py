"""
Test script to verify content acquisition handles .md files correctly
"""

import sys
import os
from pathlib import Path

# Add server src to path
sys.path.insert(0, str(Path(__file__).parent / 'server' / 'src'))

from services.phases.phase2_content_acquisition import ContentAcquisitionService, ContentItem
from services.core.google_drive_service import GoogleDriveService

def test_md_file_recognition():
    """Test that .md material files are recognized correctly"""

    # Create mock drive service (we won't actually use it for this test)
    drive_service = GoogleDriveService()

    # Create content acquisition service
    service = ContentAcquisitionService(drive_service)

    # Create mock content items simulating files from Google Drive
    mock_items = [
        ContentItem(
            id="1",
            name="LICHSU_KNTT_C12_3_6_material.md",
            mime_type="text/markdown",
            content="material 1. Nội dung material đầu tiên\nmaterial 2. Nội dung material thứ hai"
        ),
        ContentItem(
            id="2",
            name="LICHSU_KNTT_C12_3_6_questions.md",
            mime_type="text/markdown",
            content="1. Câu hỏi trắc nghiệm?\nA) Đáp án A\nB) Đáp án B\nC) Đáp án C\nD) Đáp án D\nĐáp án: A"
        ),
        ContentItem(
            id="3",
            name="LICHSU_KNTT_C12_3_6_material.txt",
            mime_type="text/plain",
            content="material 1. Nội dung material từ file txt\nmaterial 2. Nội dung material thứ hai từ txt"
        )
    ]

    # Test the parsing function
    result = service.parse_ds_from_separate_files(
        mock_items,
        subject="LICHSU",
        grade="KNTT_C12",
        chapter="3",
        lesson="6"
    )

    print("Test Results:")
    print(f"Materials found: {len(result['material'])}")
    print(f"Questions found: {len(result['questions'])}")

    print("\nMaterials:")
    for i, material in enumerate(result['material'], 1):
        print(f"{i}. {material[:100]}...")

    print("\nQuestions:")
    for i, question in enumerate(result['questions'], 1):
        print(f"{i}. {question[:100]}...")

    # Verify results
    assert len(result['material']) >= 4, f"Expected at least 4 materials, got {len(result['material'])}"
    assert len(result['questions']) >= 1, f"Expected at least 1 question, got {len(result['questions'])}"

    print("\n✅ Test passed! .md files are correctly recognized and parsed.")

if __name__ == "__main__":
    test_md_file_recognition()