"""
Example: How to use Rich Content in Question Generation
Demonstrates creating questions with images, tables, charts, and mixed content
"""

from server.src.services.core.rich_content import (
    RichQuestion,
    text, image, table, chart, latex, mixed,
    ContentType, ChartType
)
import json


def create_tn_with_chart():
    """Example TN question with chart"""
    question = RichQuestion(
        question_code="C1",
        question_type="TN",
        lesson_name="Bài 1. Chuyển động thẳng",
        chapter_number="1",
        lesson_number="1",
        level="TH",
        question_stem=mixed(
            text("Quan sát đồ thị vận tốc-thời gian sau:"),
            chart(
                ChartType.LINE,
                {
                    "title": {"text": "Đồ thị v-t"},
                    "xAxis": {
                        "name": "Thời gian (s)",
                        "type": "category",
                        "data": ["0", "2", "4", "6", "8", "10"]
                    },
                    "yAxis": {
                        "name": "Vận tốc (m/s)",
                        "type": "value"
                    },
                    "series": [{
                        "data": [0, 10, 20, 30, 40, 50],
                        "type": "line",
                        "smooth": True
                    }]
                },
                caption="Hình 1: Đồ thị vận tốc-thời gian",
                height=300
            ),
            text("Gia tốc của vật là:")
        ),
        options={
            "A": "2 m/s²",
            "B": "5 m/s²",
            "C": "10 m/s²",
            "D": "20 m/s²"
        },
        correct_answer="B",
        explanation=mixed(
            text("Từ đồ thị v-t, ta có:"),
            latex("a = \\frac{\\Delta v}{\\Delta t} = \\frac{50 - 0}{10 - 0} = 5 \\text{ m/s}^2", display="block"),
            text("Vậy gia tốc của vật là 5 m/s²")
        )
    )
    return question


def create_ds_with_table():
    """Example DS question with table"""
    question = RichQuestion(
        question_code="C2",
        question_type="DS",
        lesson_name="Bài 2. Định luật Ohm",
        chapter_number="1",
        lesson_number="2",
        level="TH",
        source_text=mixed(
            text("Thực hiện thí nghiệm đo điện trở của dây dẫn, thu được kết quả:"),
            table(
                headers=["Lần đo", "Hiệu điện thế U (V)", "Cường độ dòng điện I (A)", "Điện trở R (Ω)"],
                rows=[
                    ["1", "2.0", "0.4", "5.0"],
                    ["2", "4.0", "0.8", "5.0"],
                    ["3", "6.0", "1.2", "5.0"],
                    ["4", "8.0", "1.6", "5.0"]
                ],
                caption="Bảng 1: Kết quả đo điện trở",
                bordered=True,
                striped=True
            ),
            text("Xét các phát biểu sau:")
        ),
        statements={
            "a": {
                "text": "Điện trở dây dẫn không đổi trong suốt thí nghiệm",
                "is_correct": True
            },
            "b": {
                "text": "Cường độ dòng điện tỉ lệ nghịch với hiệu điện thế",
                "is_correct": False
            },
            "c": {
                "text": "Công suất tiêu thụ ở lần đo 4 lớn hơn lần đo 1",
                "is_correct": True
            },
            "d": {
                "text": "Dây dẫn tuân theo định luật Ohm",
                "is_correct": True
            }
        },
        explanation={
            "a": "Đúng. Từ bảng số liệu, R = 5.0 Ω ở tất cả các lần đo.",
            "b": mixed(
                text("Sai. Theo định luật Ohm: "),
                latex("I = \\frac{U}{R}", display="inline"),
                text(", cường độ dòng điện tỉ lệ thuận với hiệu điện thế.")
            ),
            "c": mixed(
                text("Đúng. Công suất "),
                latex("P = UI", display="inline"),
                text(". Lần 1: P₁ = 2.0 × 0.4 = 0.8 W. Lần 4: P₄ = 8.0 × 1.6 = 12.8 W > P₁")
            ),
            "d": "Đúng. Tỉ số U/I = const = R, chứng tỏ dây dẫn tuân theo định luật Ohm."
        }
    )
    return question


def create_tln_with_image():
    """Example TLN question with image"""
    question = RichQuestion(
        question_code="C3",
        question_type="TLN",
        lesson_name="Bài 3. Lực ma sát",
        chapter_number="1",
        lesson_number="3",
        level="VD",
        question_stem=mixed(
            text("Quan sát hình vẽ thí nghiệm:"),
            image(
                url="/images/friction_experiment.png",
                alt="Thí nghiệm lực ma sát",
                width=500,
                caption="Hình 1: Bố trí thí nghiệm đo lực ma sát"
            ),
            text("Khối gỗ có khối lượng 2 kg, hệ số ma sát trượt μ = 0.3. Lấy g = 10 m/s²."),
            text("Tính lực ma sát trượt tác dụng lên khối gỗ khi nó chuyển động.")
        ),
        correct_answer=mixed(
            text("Lực ma sát trượt:"),
            latex("F_{ms} = \\mu N = \\mu mg = 0.3 \\times 2 \\times 10 = 6 \\text{ N}", display="block"),
            text("Vậy lực ma sát trượt là 6 N")
        ),
        explanation=mixed(
            text("Áp dụng công thức lực ma sát trượt:"),
            latex("F_{ms} = \\mu N", display="block"),
            text("Trong đó:"),
            table(
                headers=["Đại lượng", "Ý nghĩa", "Giá trị"],
                rows=[
                    ["μ", "Hệ số ma sát trượt", "0.3"],
                    ["N", "Phản lực pháp tuyến", "N = mg = 20 N"],
                    ["Fms", "Lực ma sát trượt", "6 N"]
                ]
            )
        )
    )
    return question


def create_tl_with_mixed():
    """Example TL question with complex mixed content"""
    question = RichQuestion(
        question_code="C4",
        question_type="TL",
        lesson_name="Bài 4. Chuyển động ném ngang",
        chapter_number="1",
        lesson_number="4",
        level="VD",
        question_stem=mixed(
            text("Một vật được ném ngang từ độ cao h = 20m với vận tốc ban đầu v₀ = 10 m/s."),
            text("Lấy g = 10 m/s². Bỏ qua sức cản không khí."),
            image(
                url="/images/projectile_motion.png",
                alt="Chuyển động ném ngang",
                width=400,
                caption="Hình 1: Quỹ đạo chuyển động ném ngang"
            ),
            text("Hãy:"),
            text("a) Tính thời gian rơi của vật"),
            text("b) Tính tầm xa của vật"),
            text("c) Vẽ đồ thị vận tốc theo thời gian và giải thích")
        ),
        correct_answer=mixed(
            text("**a) Thời gian rơi:**"),
            text("Chuyển động theo phương thẳng đứng là rơi tự do:"),
            latex("h = \\frac{1}{2}gt^2 \\Rightarrow t = \\sqrt{\\frac{2h}{g}} = \\sqrt{\\frac{2 \\times 20}{10}} = 2 \\text{ s}", display="block"),
            
            text("\n**b) Tầm xa:**"),
            text("Chuyển động theo phương ngang là chuyển động thẳng đều:"),
            latex("L = v_0 t = 10 \\times 2 = 20 \\text{ m}", display="block"),
            
            text("\n**c) Đồ thị vận tốc:**"),
            chart(
                ChartType.LINE,
                {
                    "title": {"text": "Các thành phần vận tốc theo thời gian"},
                    "legend": {"data": ["vx (ngang)", "vy (đứng)", "v (tổng hợp)"]},
                    "xAxis": {
                        "name": "Thời gian (s)",
                        "type": "category",
                        "data": ["0", "0.5", "1.0", "1.5", "2.0"]
                    },
                    "yAxis": {
                        "name": "Vận tốc (m/s)",
                        "type": "value"
                    },
                    "series": [
                        {
                            "name": "vx (ngang)",
                            "data": [10, 10, 10, 10, 10],
                            "type": "line"
                        },
                        {
                            "name": "vy (đứng)",
                            "data": [0, 5, 10, 15, 20],
                            "type": "line"
                        },
                        {
                            "name": "v (tổng hợp)",
                            "data": [10, 11.18, 14.14, 18.03, 22.36],
                            "type": "line"
                        }
                    ]
                },
                caption="Hình 2: Đồ thị các thành phần vận tốc",
                height=350
            ),
            text("\n**Giải thích:**"),
            table(
                headers=["Thành phần", "Đặc điểm", "Công thức"],
                rows=[
                    ["vx", "Không đổi", "vx = v₀ = 10 m/s"],
                    ["vy", "Tăng đều", "vy = gt"],
                    ["v", "Tăng dần", "v = √(vx² + vy²)"]
                ],
                caption="Bảng 1: Đặc điểm các thành phần vận tốc"
            )
        )
    )
    return question


def save_examples():
    """Save all examples to JSON file"""
    examples = {
        "metadata": {
            "content_version": "2.0",
            "supports_rich_content": True,
            "description": "Examples of rich content questions"
        },
        "questions": {
            "TN": [create_tn_with_chart().to_dict()],
            "DS": [create_ds_with_table().to_dict()],
            "TLN": [create_tln_with_image().to_dict()],
            "TL": [create_tl_with_mixed().to_dict()]
        }
    }
    
    with open("rich_content_examples.json", "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    
    print("✅ Saved examples to rich_content_examples.json")


if __name__ == "__main__":
    # Create examples
    tn_q = create_tn_with_chart()
    ds_q = create_ds_with_table()
    tln_q = create_tln_with_image()
    tl_q = create_tl_with_mixed()
    
    # Print examples
    print("=" * 80)
    print("TN Question with Chart:")
    print(json.dumps(tn_q.to_dict(), ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("DS Question with Table:")
    print(json.dumps(ds_q.to_dict(), ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("TLN Question with Image:")
    print(json.dumps(tln_q.to_dict(), ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("TL Question with Mixed Content:")
    print(json.dumps(tl_q.to_dict(), ensure_ascii=False, indent=2))
    
    # Save to file
    save_examples()
