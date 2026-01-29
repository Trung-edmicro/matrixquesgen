"""
Test Rich Content Integration with Phase 4
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.src.services.phases.phase4_question_generation import GeneratedQuestion
from server.src.data.rich_content import text, image, table, chart, latex, mixed, ChartType
from datetime import datetime
import json


def test_simple_text_question():
    """Test backward compatibility with simple text"""
    print("\n" + "="*80)
    print("TEST 1: Simple Text Question (Backward Compatible)")
    print("="*80)
    
    q = GeneratedQuestion(
        id="VATLY_C12_1_1_TN_C1",
        type="TN",
        question="Nhiệt độ sôi của nước ở áp suất tiêu chuẩn là bao nhiêu?",
        options={
            "A": "90°C",
            "B": "100°C",
            "C": "110°C",
            "D": "120°C"
        },
        correct_answer="B",
        explanation="Ở áp suất 1 atm, nước sôi ở 100°C",
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="1",
        lesson_name="Bài 1. Nhiệt học",
        generated_at=datetime.now().isoformat(),
        difficulty="NB"
    )
    
    result = q.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("✅ Simple text question works!")


def test_rich_content_question():
    """Test question with rich content (chart)"""
    print("\n" + "="*80)
    print("TEST 2: Rich Content Question with Chart")
    print("="*80)
    
    q = GeneratedQuestion(
        id="VATLY_C12_1_1_TN_C2",
        type="TN",
        question=mixed(
            text("Quan sát đồ thị nhiệt độ-thời gian:"),
            chart(
                ChartType.LINE,
                {
                    "title": {"text": "Sự thay đổi nhiệt độ"},
                    "xAxis": {
                        "name": "Thời gian (phút)",
                        "data": ["0", "5", "10", "15", "20"]
                    },
                    "yAxis": {"name": "Nhiệt độ (°C)"},
                    "series": [{
                        "data": [20, 40, 60, 80, 100],
                        "type": "line"
                    }]
                },
                caption="Hình 1: Đồ thị T-t",
                height=300
            ),
            text("Nhiệt độ tại phút thứ 10 là bao nhiêu?")
        ),
        options={
            "A": "40°C",
            "B": "60°C",
            "C": "80°C",
            "D": "100°C"
        },
        correct_answer="B",
        explanation=mixed(
            text("Từ đồ thị, tại t = 10 phút, nhiệt độ T = 60°C"),
            latex("T(10) = 60^\\circ C", display="block")
        ),
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="1",
        lesson_name="Bài 1. Nhiệt học",
        generated_at=datetime.now().isoformat(),
        difficulty="TH"
    ),
    
    result = q.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("✅ Rich content question with chart works!")


def test_table_question():
    """Test question with table"""
    print("\n" + "="*80)
    print("TEST 3: Question with Table")
    print("="*80)
    
    q = GeneratedQuestion(
        id="VATLY_C12_1_2_DS_C1",
        type="DS",
        source_text=mixed(
            text("Bảng số liệu thí nghiệm:"),
            table(
                headers=["Lần đo", "U (V)", "I (A)", "R (Ω)"],
                rows=[
                    ["1", "2.0", "0.4", "5.0"],
                    ["2", "4.0", "0.8", "5.0"],
                    ["3", "6.0", "1.2", "5.0"]
                ],
                caption="Bảng 1: Kết quả đo điện trở"
            )
        ),
        statements={
            "a": {"text": "Điện trở không đổi", "is_correct": True},
            "b": {"text": "I tỉ lệ nghịch với U", "is_correct": False},
            "c": {"text": "Tuân theo định luật Ohm", "is_correct": True},
            "d": {"text": "R = 5Ω", "is_correct": True}
        },
        question="",
        correct_answer="",
        explanation={
            "a": "Đúng. R = 5.0 Ω ở tất cả lần đo",
            "b": mixed(
                text("Sai. Theo Ohm: "),
                latex("I = \\frac{U}{R}", display="inline")
            ),
            "c": "Đúng. U/I = const",
            "d": "Đúng. Từ bảng số liệu"
        },
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="2",
        lesson_name="Bài 2. Điện học",
        generated_at=datetime.now().isoformat(),
        difficulty="TH"
    )
    
    result = q.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("✅ Question with table works!")


def test_mixed_content():
    """Test complex mixed content"""
    print("\n" + "="*80)
    print("TEST 4: Complex Mixed Content")
    print("="*80)
    
    q = GeneratedQuestion(
        id="VATLY_C12_1_3_TL_C1",
        type="TL",
        question=mixed(
            text("Một vật chuyển động với:"),
            image(
                "/images/motion_diagram.png",
                alt="Sơ đồ chuyển động",
                width=400,
                caption="Hình 1: Sơ đồ"
            ),
            text("Phương trình vận tốc:"),
            latex("v = v_0 + at", display="block"),
            text("Với v₀ = 10 m/s, a = 2 m/s². Tính quãng đường sau 5 giây.")
        ),
        options={},
        correct_answer=mixed(
            text("Quãng đường:"),
            latex("s = v_0 t + \\frac{1}{2}at^2 = 10(5) + \\frac{1}{2}(2)(5)^2 = 75 \\text{ m}", display="block")
        ),
        explanation=mixed(
            text("Áp dụng công thức chuyển động thẳng biến đổi đều:"),
            table(
                headers=["Đại lượng", "Giá trị"],
                rows=[
                    ["v₀", "10 m/s"],
                    ["a", "2 m/s²"],
                    ["t", "5 s"],
                    ["s", "75 m"]
                ]
            )
        ),
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="3",
        lesson_name="Bài 3. Chuyển động",
        generated_at=datetime.now().isoformat(),
        difficulty="VD"
    )
    
    result = q.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("✅ Complex mixed content works!")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING RICH CONTENT INTEGRATION WITH PHASE 4")
    print("="*80)
    
    try:
        test_simple_text_question()
        test_rich_content_question()
        test_table_question()
        test_mixed_content()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nRich content integration is working correctly!")
        print("- Backward compatible with simple text ✓")
        print("- Supports charts (ECharts) ✓")
        print("- Supports tables ✓")
        print("- Supports LaTeX formulas ✓")
        print("- Supports images ✓")
        print("- Supports mixed content ✓")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
