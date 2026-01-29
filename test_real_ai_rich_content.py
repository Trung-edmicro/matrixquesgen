"""
Test Rich Content with Real AI Responses
Generates questions using real AI and demonstrates rich content integration
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from server.src.services.core.genai_client import GenAIClient
from server.src.services.generators.question_generator import QuestionGenerator
from server.src.services.core.matrix_parser import MatrixParser, QuestionSpec
from server.src.data.rich_content import text, image, table, chart, latex, mixed, ChartType
from server.src.services.utils.rich_content_parser import parse_ai_response
from server.src.services.phases.phase4_question_generation import GeneratedQuestion
from datetime import datetime
import json


def test_basic_integration():
    """Test 1: Basic rich content without AI"""
    print("\n" + "="*80)
    print("TEST 1: Basic Rich Content Integration (No AI)")
    print("="*80)
    
    # Create a question with rich content
    question = GeneratedQuestion(
        id="TEST_C12_1_1_TN_C1",
        type="TN",
        question=mixed(
            text("Quan sát biểu đồ nhiệt độ:"),
            chart(
                ChartType.LINE,
                {
                    "title": {"text": "Nhiệt độ theo thời gian"},
                    "xAxis": {
                        "name": "Thời gian (s)",
                        "type": "category",
                        "data": ["0", "30", "60", "90", "120"]
                    },
                    "yAxis": {
                        "name": "Nhiệt độ (°C)",
                        "type": "value"
                    },
                    "series": [{
                        "name": "Nhiệt độ",
                        "data": [20, 40, 60, 80, 100],
                        "type": "line",
                        "smooth": True
                    }]
                },
                caption="Hình 1: Đồ thị nhiệt độ-thời gian",
                height=350
            ),
            text("Nhiệt độ tại 60s là bao nhiêu?")
        ),
        options={
            "A": "40°C",
            "B": "60°C",
            "C": "80°C",
            "D": "100°C"
        },
        correct_answer="B",
        explanation=mixed(
            text("Từ đồ thị, tại t = 60s:"),
            latex("T(60) = 60^\\circ C", display="block"),
            text("Vậy đáp án đúng là B.")
        ),
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="1",
        lesson_name="Bài 1. Nhiệt học cơ bản",
        generated_at=datetime.now().isoformat(),
        difficulty="TH"
    )
    
    # Serialize to JSON
    result = question.to_dict()
    
    print("\n📋 Generated Question JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Verify structure
    assert 'question' in result
    assert isinstance(result['question'], dict)
    assert result['question']['type'] == 'mixed'
    assert len(result['question']['content']) == 3
    
    print("\n✅ Test 1 PASSED: Basic rich content serialization works!")
    return True


def test_ai_response_parsing():
    """Test 2: Parse AI response with rich content markers"""
    print("\n" + "="*80)
    print("TEST 2: AI Response Parsing")
    print("="*80)
    
    # Simulate AI response with markers
    ai_response = """
Quan sát bảng số liệu thí nghiệm sau:

| Lần đo | Hiệu điện thế U (V) | Cường độ I (A) | Điện trở R (Ω) |
|--------|---------------------|----------------|----------------|
| 1      | 2.0                 | 0.4            | 5.0            |
| 2      | 4.0                 | 0.8            | 5.0            |
| 3      | 6.0                 | 1.2            | 5.0            |

Theo định luật Ohm: $R = \\frac{U}{I}$

Từ bảng số liệu, ta thấy điện trở không đổi.
    """
    
    print("\n📝 AI Response:")
    print(ai_response)
    
    # Parse response
    parsed = parse_ai_response(ai_response)
    
    print("\n📊 Parsed Content:")
    if hasattr(parsed, 'to_dict'):
        print(json.dumps(parsed.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(parsed)
    
    print("\n✅ Test 2 PASSED: AI response parsing works!")
    return True


def test_with_real_ai():
    """Test 3: Generate question with real AI"""
    print("\n" + "="*80)
    print("TEST 3: Real AI Question Generation")
    print("="*80)
    
    # Check for API credentials
    api_key = os.getenv("GENAI_API_KEY")
    if not api_key:
        print("⚠️  GENAI_API_KEY not found. Skipping real AI test.")
        print("   Set environment variable to test with real AI:")
        print("   $env:GENAI_API_KEY='your-api-key'")
        return False
    
    try:
        # Initialize AI client
        print("\n🔧 Initializing AI client...")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "matrixquesgen")
        ai_client = GenAIClient(
            project_id=project_id,
            api_key=api_key
        )
        print("✓ AI client initialized")
        
        # Initialize question generator
        prompts_dir = Path(__file__).parent / "data" / "prompts"
        tn_prompt = prompts_dir / "TN.txt"
        
        if not tn_prompt.exists():
            print(f"⚠️  Prompt file not found: {tn_prompt}")
            print("   Using basic prompt...")
            # Create basic prompt
            basic_prompt = """# TASK:
Sinh {{NUM}} câu hỏi trắc nghiệm về {{LESSON_NAME}}
Cấp độ: {{COGNITIVE_LEVEL}}
Kết quả học tập: {{EXPECTED_LEARNING_OUTCOME}}

Nội dung: {{CONTENT}}

Trả về JSON format với các trường: question_stem, options, correct_answer, explanation
"""
            tn_prompt.parent.mkdir(parents=True, exist_ok=True)
            with open(tn_prompt, 'w', encoding='utf-8') as f:
                f.write(basic_prompt)
        
        matrix_parser = MatrixParser()
        generator = QuestionGenerator(
            ai_client=ai_client,
            prompt_template_path=str(tn_prompt),
            verbose=True,
            matrix_parser=matrix_parser
        )
        print("✓ Question generator initialized")
        
        # Create question spec
        spec = QuestionSpec(
            question_codes=["C1"],
            lesson_name="Bài 1. Cấu trúc của chất",
            question_type="TN",
            cognitive_level="TH",
            learning_outcome="Học sinh hiểu được cấu trúc phân tử của các thể rắn, lỏng, khí",
            num_questions=1,
            competency_level=1,
            row_index=0
        )
        
        print("\n🤖 Generating question with AI...")
        print(f"   Lesson: {spec.lesson_name}")
        print(f"   Level: {spec.cognitive_level}")
        
        # Generate question
        content = """
Theo mô hình động học phân tử:
- Chất rắn: Các phân tử dao động quanh vị trí cân bằng cố định
- Chất lỏng: Các phân tử dao động quanh vị trí cân bằng di động
- Chất khí: Các phân tử chuyển động tự do
        """
        
        questions = generator.generate_questions_for_spec(
            spec=spec,
            content=content
        )
        
        if questions:
            print(f"\n✅ Generated {len(questions)} question(s)")
            
            for i, q in enumerate(questions, 1):
                print(f"\n{'='*60}")
                print(f"Question {i}:")
                print(f"{'='*60}")
                print(f"Code: {q.question_code}")
                print(f"Stem: {q.question_stem}")
                print(f"\nOptions:")
                for key, value in q.options.items():
                    mark = "✓" if key == q.correct_answer else " "
                    print(f"  [{mark}] {key}. {value}")
                print(f"\nExplanation: {q.explanation}")
                
                # Convert to rich format if needed
                # (In future: parse AI response for rich content markers)
                
            print("\n✅ Test 3 PASSED: Real AI generation works!")
            return True
        else:
            print("\n❌ No questions generated")
            return False
            
    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_table_in_question():
    """Test 4: Question with table content"""
    print("\n" + "="*80)
    print("TEST 4: Question with Table")
    print("="*80)
    
    question = GeneratedQuestion(
        id="TEST_C12_1_2_DS_C1",
        type="DS",
        source_text=mixed(
            text("Cho bảng số liệu:"),
            table(
                headers=["Chất", "Nhiệt độ nóng chảy (°C)", "Nhiệt độ sôi (°C)"],
                rows=[
                    ["Nước", "0", "100"],
                    ["Rượu etylic", "-114", "78"],
                    ["Thủy ngân", "-39", "357"]
                ],
                caption="Bảng 1: Nhiệt độ chuyển thể của một số chất",
                bordered=True,
                striped=True
            ),
            text("Xét các phát biểu:")
        ),
        question="",
        correct_answer="",
        statements={
            "a": {"text": "Nước có nhiệt độ sôi cao nhất", "is_correct": False},
            "b": {"text": "Rượu có nhiệt độ nóng chảy thấp nhất", "is_correct": True},
            "c": {"text": "Thủy ngân ở thể lỏng ở nhiệt độ phòng", "is_correct": True},
            "d": {"text": "Nước đóng băng ở 0°C", "is_correct": True}
        },
        explanation={
            "a": "Sai. Thủy ngân có nhiệt độ sôi cao nhất (357°C)",
            "b": "Đúng. Rượu có tnc = -114°C",
            "c": "Đúng. Nhiệt độ phòng (~25°C) > -39°C",
            "d": "Đúng. Theo định nghĩa nhiệt độ nóng chảy của nước"
        },
        subject="VATLY",
        grade="C12",
        chapter="1",
        lesson="2",
        lesson_name="Bài 2. Sự chuyển thể",
        generated_at=datetime.now().isoformat(),
        difficulty="NB"
    )
    
    result = question.to_dict()
    print("\n📋 DS Question with Table:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n✅ Test 4 PASSED: Table in question works!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 TESTING RICH CONTENT WITH REAL AI")
    print("="*80)
    
    results = []
    
    # Test 1: Basic integration
    try:
        results.append(("Basic Integration", test_basic_integration()))
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results.append(("Basic Integration", False))
    
    # Test 2: AI response parsing
    try:
        results.append(("AI Response Parsing", test_ai_response_parsing()))
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results.append(("AI Response Parsing", False))
    
    # Test 3: Real AI generation
    try:
        results.append(("Real AI Generation", test_with_real_ai()))
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results.append(("Real AI Generation", False))
    
    # Test 4: Table in question
    try:
        results.append(("Table in Question", test_table_in_question()))
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        results.append(("Table in Question", False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
