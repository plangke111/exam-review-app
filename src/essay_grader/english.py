"""英语作文批改器"""

from .base import BaseGrader


class EnglishGrader(BaseGrader):
    """批改英语一大/小作文"""

    def grade_big(self, student_answer: str, prompt: str = "",
                  exam_type: str = "英语一", max_score: int = 20,
                  word_count: int = None, reference_notes: str = "",
                  handwriting_quality: str = "unknown") -> dict:
        """批改大作文（英语一20分/英语二15分）"""
        system_prompt = self._get_prompt("english_big")
        input_json = {
            "exam_type": exam_type,
            "prompt": prompt,
            "student_answer": student_answer,
            "max_score": max_score,
            "handwriting_quality": handwriting_quality,
            "reference_notes": reference_notes,
        }
        if word_count is not None:
            input_json["word_count"] = word_count
        return self._call_api(system_prompt, input_json)

    def grade_small(self, student_answer: str, prompt: str = "",
                    exam_type: str = "英语一", max_score: int = 10,
                    task_type_hint: str = "", reference_notes: str = "",
                    handwriting_quality: str = "unknown") -> dict:
        """批改小作文（满分10分）"""
        system_prompt = self._get_prompt("english_small")
        input_json = {
            "prompt": prompt,
            "student_answer": student_answer,
            "exam_type": exam_type,
            "max_score": max_score,
            "task_type_hint": task_type_hint,
            "handwriting_quality": handwriting_quality,
            "reference_notes": reference_notes,
        }
        return self._call_api(system_prompt, input_json)
