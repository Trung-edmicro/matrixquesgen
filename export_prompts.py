"""
Xuất toàn bộ prompt đã mapping ra file .txt để kiểm tra.
Chạy từ thư mục gốc của project:

    python export_prompts.py data/matrix/enriched_matrix_DIALY_KNTT_C12.json
    python export_prompts.py data/matrix/enriched_matrix_LICHSU_KNTT_C12.json --types TN DS
    python export_prompts.py data/matrix/enriched_matrix_DIALY_KNTT_C12.json --out data/test_output/check.txt
"""
import sys
import argparse
from pathlib import Path

# Thêm server/src vào sys.path để import service
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'server' / 'src'))


def main():
    parser = argparse.ArgumentParser(description='Xuất prompt đã mapping để kiểm tra.')
    parser.add_argument('enriched_json',
                        nargs='?',
                        default=None,
                        help='Đường dẫn tới enriched_matrix_*.json (mặc định: hỏi)')
    parser.add_argument('--out', default=None,
                        help='File đầu ra .txt (mặc định: data/test_output/<name>_prompts_<ts>.txt)')
    parser.add_argument('--types', nargs='+', default=None,
                        choices=['TN', 'DS', 'TLN', 'TL'],
                        help='Chỉ xuất các loại câu hỏi này (mặc định: tất cả)')
    parser.add_argument('--prompt-dir', default=None,
                        help='Thư mục chứa file prompt template (TN.txt, DS.txt,...)')
    args = parser.parse_args()

    # Resolve enriched JSON
    enriched_json = args.enriched_json
    if not enriched_json:
        # Tự tìm file mới nhất trong data/matrix/
        candidates = sorted(
            (ROOT / 'data' / 'matrix').glob('enriched_matrix_*.json'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if not candidates:
            print('❌ Không tìm thấy enriched_matrix_*.json trong data/matrix/')
            sys.exit(1)
        enriched_json = str(candidates[0])
        print(f'ℹ️  Sử dụng file mới nhất: {enriched_json}')

    enriched_path = Path(enriched_json)
    if not enriched_path.exists():
        print(f'❌ File không tồn tại: {enriched_json}')
        sys.exit(1)

    # Resolve prompt dir
    prompt_dir = args.prompt_dir
    if not prompt_dir:
        # Tìm thư mục data/prompts gần nhất
        default_dir = ROOT / 'data' / 'prompts'
        if default_dir.exists():
            prompt_dir = str(default_dir)
        else:
            print('⚠️  Không tìm thấy data/prompts/ — template sẽ không được load')

    # Import và chạy
    from services.generators.prompt_builder_service import PromptBuilderService

    pbs = PromptBuilderService(prompt_dir=prompt_dir, verbose=False)

    output_path = pbs.export_prompts_from_enriched_json(
        enriched_matrix_path=str(enriched_path),
        output_path=args.out,
        question_types=args.types
    )

    print(f'\n📄 Mở file để kiểm tra:\n   {output_path}')


if __name__ == '__main__':
    main()
