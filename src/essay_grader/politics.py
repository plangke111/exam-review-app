"""政治分析题批改器"""

from .base import BaseGrader


class PoliticsGrader(BaseGrader):
    """批改政治分析题（每题10分）"""

    def grade_single(self, student_answer: str, question: str = "",
                     materials: str = "", max_score: int = 10,
                     subject_hint: str = "",
                     reference_answer: str = "",
                     reference_scoring_points: str = "",
                     current_affairs_context: str = "") -> dict:
        """批改单道政治分析题"""
        system_prompt = self._get_prompt("politics")
        input_json = {
            "question": question,
            "materials": materials,
            "student_answer": student_answer,
            "max_score": max_score,
            "subject_hint": subject_hint,
            "reference_answer": reference_answer,
            "reference_scoring_points": reference_scoring_points,
            "current_affairs_context": current_affairs_context,
        }
        return self._call_api(system_prompt, input_json)

    def grade_set(self, answers: list[dict]) -> dict:
        """批改整套政治分析题（5道）"""
        results = []
        for a in answers:
            r = self.grade_single(
                student_answer=a.get("student_answer", ""),
                question=a.get("question", ""),
                materials=a.get("materials", ""),
                max_score=a.get("max_score", 10),
                subject_hint=a.get("subject_hint", ""),
                reference_answer=a.get("reference_answer", ""),
                reference_scoring_points=a.get("reference_scoring_points", ""),
                current_affairs_context=a.get("current_affairs_context", ""),
            )
            results.append(r)
        total = sum(r.get("score", 0) for r in results)
        total_max = sum(r.get("max_score", 10) for r in results)
        return {"各题": results, "总分": total, "满分": total_max}
