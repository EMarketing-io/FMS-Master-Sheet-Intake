from typing import Dict, Any
from datetime import date
from docx import Document
import io


def generate_docx(summary_data: Dict[str, Any], company_name: str, meeting_date, mode: str = "full") -> io.BytesIO:
    doc = Document()

    if isinstance(meeting_date, date):
        meeting_date = meeting_date.strftime("%d-%m-%Y")

    # Title
    if mode == "full":
        doc.add_heading(f"{company_name} Meeting Notes", level=0)
        p = doc.add_paragraph(f"Date: {meeting_date}")
        p.alignment = 2
    elif mode == "mom":
        doc.add_heading(f"{company_name} - MoM", level=0)
    elif mode == "action":
        doc.add_heading(f"{company_name} - Action Points", level=0)

    # 1) MoM
    if mode in ["full", "mom"]:
        doc.add_heading("1. Minutes of the Meeting (MoM)", level=1)
        for point in summary_data.get("mom", []):
            if point and str(point).strip():
                doc.add_paragraph(str(point).strip(), style="List Bullet")

    # 2) To-Do (only in full)
    if mode == "full":
        doc.add_heading("2. To-Do List", level=1)
        for task in summary_data.get("todo_list", []):
            if task and str(task).strip():
                doc.add_paragraph(str(task).strip(), style="List Bullet")

    # 3) Action Points
    if mode in ["full", "action"]:
        doc.add_heading("3. Action Points / Action Plan", level=1)
        section_titles = {
            "decision_made": "Key Decisions Made",
            "key_services_to_promote": "Key Services to Promote",
            "target_geography": "Target Geography",
            "budget_and_timeline": "Budget and Timeline",
            "lead_management_strategy": "Lead Management Strategy",
            "next_steps_and_ownership": "Next Steps and Ownership",
        }
        action_plan = summary_data.get("action_plan", {}) or {}
        for key, title in section_titles.items():
            items = action_plan.get(key, [])
            if items:
                doc.add_heading(title, level=2)
                for item in items:
                    if item and str(item).strip():
                        doc.add_paragraph(str(item).strip(), style="List Bullet")

    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out