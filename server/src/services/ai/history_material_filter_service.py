"""
History Material Filter Service
Service for filtering DS question materials using AI based on learning outcomes
Used for subjects that require material filtering (e.g., LICHSU)
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path

from ..core.genai_client import GenAIClient


class HistoryMaterialFilterService:
    """Service for filtering DS question materials using AI"""

    def __init__(self, genai_client: Optional[GenAIClient] = None):
        # Use the provided client, or create one from configured AI provider
        if genai_client:
            self.genai_client = genai_client
        else:
            try:
                from ..core.ai_provider_settings import create_ai_client
                self.genai_client = create_ai_client()
                print("✅ Initialized AI client for History material filtering")
            except Exception as e:
                print(f"❌ Failed to initialize AI client for History material filtering: {e}")
                self.genai_client = None

        self.prompts_dir = Path(__file__).parent.parent / 'prompts' / 'history_subject'
        self.filter_prompt_path = self.prompts_dir / 'filter_material.md'

    def _load_filter_prompt(self) -> str:
        """Load the filter material prompt"""
        try:
            with open(self.filter_prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading filter material prompt: {e}")
            return ""

    def filter_materials(
        self,
        lesson_name: str,
        question_code: str,
        statements: List[Dict],
        materials_list: List[str]
    ) -> List[str]:
        """Filter materials using AI to find the most relevant ones for the DS question

        Args:
            lesson_name: Name of the lesson (bai hoc)
            question_code: DS question code (e.g., "C1", "C2")
            statements: List of statement dicts with keys: label, cognitive_level, learning_outcome
            materials_list: List of material texts from Drive to filter from

        Returns:
            List of 2-3 selected material strings (original text, not modified)
            Falls back to first 2 materials if AI fails or returns empty
        """
        try:
            if not materials_list:
                print("⚠️  No materials to filter")
                return []

            # Load prompt template
            prompt_template = self._load_filter_prompt()
            if not prompt_template:
                print("⚠️  Filter material prompt template is empty, returning first 2 materials")
                return materials_list[:2]

            # Extract statement info (up to 4 statements: a, b, c, d)
            stmt_map = {s.get('label', ''): s for s in statements}
            labels = ['a', 'b', 'c', 'd']

            def get_level(label):
                return stmt_map.get(label, {}).get('cognitive_level', '')

            def get_outcome(label):
                return stmt_map.get(label, {}).get('learning_outcome', '')

            # Format material list as numbered string for the prompt
            material_str = "\n\n".join(
                f"Tư liệu {i+1}:\n{m}" for i, m in enumerate(materials_list)
            )

            # Fill variables in prompt
            filled_prompt = prompt_template.replace('{{QUESTION_CODE}}', question_code)
            filled_prompt = filled_prompt.replace('{{LESSON_NAME}}', lesson_name)
            filled_prompt = filled_prompt.replace('{{COGNITIVE_LEVEL_A}}', get_level('a'))
            filled_prompt = filled_prompt.replace('{{COGNITIVE_LEVEL_B}}', get_level('b'))
            filled_prompt = filled_prompt.replace('{{COGNITIVE_LEVEL_C}}', get_level('c'))
            filled_prompt = filled_prompt.replace('{{COGNITIVE_LEVEL_D}}', get_level('d'))
            filled_prompt = filled_prompt.replace('{{EXPECTED_LEARNING_OUTCOME_A}}', get_outcome('a'))
            filled_prompt = filled_prompt.replace('{{EXPECTED_LEARNING_OUTCOME_B}}', get_outcome('b'))
            filled_prompt = filled_prompt.replace('{{EXPECTED_LEARNING_OUTCOME_C}}', get_outcome('c'))
            filled_prompt = filled_prompt.replace('{{EXPECTED_LEARNING_OUTCOME_D}}', get_outcome('d'))
            filled_prompt = filled_prompt.replace('{{MATERIAL}}', material_str)

            print(f"\n🔍 Filtering {len(materials_list)} materials for DS {question_code} ({lesson_name[:60]}...)")

            # Check if client is available
            if not self.genai_client:
                print(f"⚠️  GenAI client not available, fallback to first 2 materials")
                return materials_list[:2]

            # Call AI
            response_text = self.genai_client.generate_content(
                prompt=filled_prompt,
                system_instruction="You are an AI assistant specialized in filtering historical materials for DS questions. Return only a JSON array of selected material strings copied verbatim from the input list."
            )

            if not response_text or not response_text.strip():
                print(f"⚠️  AI filtering returned empty response, fallback to first 2 materials")
                return materials_list[:2]

            # Parse response
            content = response_text.strip()

            # Remove markdown code blocks if present
            if '```' in content:
                lines = content.split('\n')
                start_idx, end_idx = 0, len(lines) - 1
                for i, line in enumerate(lines):
                    if line.strip().startswith('['):
                        start_idx = i
                        break
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip().endswith(']'):
                        end_idx = i
                        break
                content = '\n'.join(lines[start_idx:end_idx + 1])

            try:
                selected_materials = json.loads(content)

                if not isinstance(selected_materials, list):
                    raise ValueError("Response is not a list")

                if len(selected_materials) == 0:
                    print(f"⚠️  AI found no matching materials, fallback to first 2")
                    return materials_list[:2]

                # Clamp to 2-3 results
                if len(selected_materials) > 3:
                    print(f"⚠️  AI returned {len(selected_materials)} materials (> 3), trimming to 3")
                    selected_materials = selected_materials[:3]

                print(f"✅ AI filtered to {len(selected_materials)} materials for DS {question_code}")
                return selected_materials

            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse AI response as JSON: {e}")
                print(f"   Response preview: {content[:300]}")
                print(f"   Fallback: returning first 2 materials")
                return materials_list[:2]

        except Exception as e:
            print(f"❌ Error in filter_materials for DS {question_code}: {e}")
            import traceback
            traceback.print_exc()
            return materials_list[:2] if len(materials_list) >= 2 else materials_list
