"""
Math Template Filter Service
Service for filtering question templates using AI based on cognitive level and learning outcomes
Only used for TOAN subject
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path

from ..core.genai_client import GenAIClient


class MathTemplateFilterService:
    """Service for filtering Math question templates using AI"""

    def __init__(self, genai_client: Optional[GenAIClient] = None):
        # Use the provided client, or create one from configured AI provider
        if genai_client:
            self.genai_client = genai_client
        else:
            try:
                from ..core.ai_provider_settings import create_ai_client
                self.genai_client = create_ai_client()
                print("✅ Initialized AI client for Math template filtering")
            except Exception as e:
                print(f"❌ Failed to initialize AI client for Math template filtering: {e}")
                self.genai_client = None
        
        self.prompts_dir = Path(__file__).parent.parent / 'prompts' / 'math_subject'
        self.filter_prompt_path = self.prompts_dir / 'filter_question_template.md'
        self.info_cognitive_dir = self.prompts_dir / 'info_cognitive_level'

    def _load_filter_prompt(self) -> str:
        """Load the filter question template prompt"""
        try:
            with open(self.filter_prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading filter prompt: {e}")
            return ""

    def _load_cognitive_level_info(self, question_type: str, cognitive_level: str) -> str:
        """Load cognitive level information for specific question type and level
        
        Args:
            question_type: Question type (TN, DS, TLN, TL)
            cognitive_level: Cognitive level (NB, TH, VD)
        
        Returns:
            Content of the cognitive level info file
        """
        try:
            # Path: info_cognitive_level/{question_type}/{cognitive_level}.md
            info_path = self.info_cognitive_dir / question_type / f"{cognitive_level}.md"
            
            if not info_path.exists():
                print(f"⚠️  Cognitive level info not found: {info_path}")
                return f"Cấp độ {cognitive_level}"
            
            with open(info_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading cognitive level info: {e}")
            return f"Cấp độ {cognitive_level}"

    def filter_question_templates(
        self,
        question_type: str,
        cognitive_level: str,
        expected_learning_outcome: str,
        question_list: List[str]
    ) -> List[str]:
        """Filter question templates using AI
        
        Args:
            question_type: Type of question (TN, DS, TLN, TL)
            cognitive_level: Cognitive level (NB, TH, VD)
            expected_learning_outcome: Expected learning outcome description
            question_list: Full list of question templates to filter
        
        Returns:
            List of 5-10 filtered question templates
        """
        try:
            if not question_list:
                print("⚠️  No questions to filter")
                return []

            # Load prompt template
            prompt_template = self._load_filter_prompt()
            if not prompt_template:
                print("⚠️  Filter prompt template is empty, returning first 5 questions")
                return question_list[:5]

            # Load cognitive level info
            cognitive_level_info = self._load_cognitive_level_info(question_type, cognitive_level)

            # Format question list as string
            question_list_str = json.dumps(question_list, ensure_ascii=False, indent=2)

            # Fill variables in prompt
            filled_prompt = prompt_template.replace('{{QUESTION_TYPE}}', question_type)
            filled_prompt = filled_prompt.replace('{{COGNITIVE_LEVEL}}', cognitive_level)
            filled_prompt = filled_prompt.replace('{{INFO_COGNITIVE_LEVEL}}', cognitive_level_info)
            filled_prompt = filled_prompt.replace('{{EXPECTED_LEARNING_OUTCOME}}', expected_learning_outcome)
            filled_prompt = filled_prompt.replace('{{QUESTION_LIST_TEMPLATE}}', question_list_str)

            print(f"\n🤖 Filtering {len(question_list)} questions for {question_type}-{cognitive_level}...")
            print(f"   Expected outcome: {expected_learning_outcome[:100]}...")

            # Check if client is available
            if not self.genai_client:
                print(f"⚠️  GenAI client not available, fallback to first 5 questions")
                return question_list[:5]

            # Call AI
            response_text = self.genai_client.generate_content(
                prompt=filled_prompt,
                system_instruction="You are an AI assistant specialized in filtering Math question templates based on cognitive levels and learning outcomes. Return only a JSON array of selected questions."
            )

            if not response_text or not response_text.strip():
                print(f"⚠️  AI filtering returned empty response")
                print(f"   Fallback: returning first 5 questions")
                return question_list[:5]

            # Parse response
            content = response_text.strip()
            
            # Try to parse as JSON array
            try:
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    lines = content.split('\n')
                    # Find first line that starts with [ and last line that ends with ]
                    start_idx = 0
                    end_idx = len(lines) - 1
                    for i, line in enumerate(lines):
                        if line.strip().startswith('['):
                            start_idx = i
                            break
                    for i in range(len(lines) - 1, -1, -1):
                        if lines[i].strip().endswith(']'):
                            end_idx = i
                            break
                    content = '\n'.join(lines[start_idx:end_idx + 1])

                filtered_questions = json.loads(content)
                
                if not isinstance(filtered_questions, list):
                    raise ValueError("Response is not a list")
                
                # Validate: should be 5-10 questions
                if len(filtered_questions) < 5:
                    print(f"⚠️  AI returned only {len(filtered_questions)} questions (< 5)")
                    # Pad with random questions from original list
                    remaining = [q for q in question_list if q not in filtered_questions]
                    import random
                    additional_needed = 5 - len(filtered_questions)
                    if remaining and additional_needed > 0:
                        additional = random.sample(remaining, min(additional_needed, len(remaining)))
                        filtered_questions.extend(additional)
                
                if len(filtered_questions) > 10:
                    print(f"⚠️  AI returned {len(filtered_questions)} questions (> 10), trimming to 10")
                    filtered_questions = filtered_questions[:10]

                print(f"✅ AI filtered to {len(filtered_questions)} questions")
                return filtered_questions

            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse AI response as JSON: {e}")
                print(f"   Response preview: {content[:500]}")
                print(f"   Fallback: returning first 5 questions")
                return question_list[:5]

        except Exception as e:
            print(f"❌ Error in filter_question_templates: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return first 5 questions
            return question_list[:5] if len(question_list) >= 5 else question_list

    def filter_templates_for_lesson(
        self,
        question_specs: Dict,
        question_type: str,
        raw_questions_by_level: Dict[str, List[str]]
    ) -> int:
        """Filter templates for all specs in a lesson
        
        Args:
            question_specs: Question specifications (TN/TLN/TL structure with levels)
            question_type: Type of question (TN, TLN, TL)
            raw_questions_by_level: Dict mapping level (NB/TH/VD) to raw question lists
        
        Returns:
            Number of questions filtered
        """
        questions_filtered = 0

        try:
            # Iterate through levels
            for level in ['NB', 'TH', 'VD']:
                if level not in question_specs or level not in raw_questions_by_level:
                    continue

                level_specs = question_specs[level]
                raw_questions = raw_questions_by_level[level]

                if not raw_questions:
                    print(f"   No raw questions for {question_type}-{level}")
                    continue

                # Filter for each spec
                for spec in level_specs:
                    learning_outcome = spec.get('learning_outcome', '')
                    
                    # Filter using AI
                    filtered = self.filter_question_templates(
                        question_type=question_type,
                        cognitive_level=level,
                        expected_learning_outcome=learning_outcome,
                        question_list=raw_questions
                    )

                    # Update spec with filtered templates
                    spec['question_template'] = filtered
                    questions_filtered += len(filtered)

            return questions_filtered

        except Exception as e:
            print(f"Error filtering templates for lesson: {e}")
            return 0
