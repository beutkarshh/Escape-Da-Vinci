from fpdf import FPDF
from typing import Any, Dict, List
from datetime import datetime

# -----------------------------
# Palette / constants
# -----------------------------
PAL = {
    "brand": (25, 118, 210),      # banner blue
    "ink": (28, 28, 30),          # main text
    "muted": (95, 104, 112),      # labels / subtle text
    "line": (215, 220, 225),      # borders
    "soft": (246, 248, 251),      # card bg
    "chip": (242, 245, 250),      # chip bg
    "ok": (76, 175, 80),
    "warn": (255, 193, 7),
    "bad": (244, 67, 54),
    "wm_light": (225, 228, 232),  # watermark title
    "wm_text": (130, 138, 145),   # watermark subtitle
}

# -----------------------------
# Helpers
# -----------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def pct_text(p) -> str:
    try:
        return f"{clamp(float(p), 0, 100):.0f}%"
    except Exception:
        return "0%"

def safe_str(v: Any, max_token_len: int = 60) -> str:
    s = "" if v is None else str(v)
    out = []
    for tok in s.split():
        if len(tok) > max_token_len:
            out.append(" ".join(tok[i:i + max_token_len] for i in range(0, len(tok), max_token_len)))
        else:
            out.append(tok)
    if out:
        return " ".join(out)
    if len(s) > max_token_len:
        return " ".join(s[i:i + max_token_len] for i in range(0, len(s), max_token_len))
    return s

# -----------------------------
# PDF class
# -----------------------------
class MedsAIReport(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(16, 18, 16)
        self.set_auto_page_break(True, 20)
        self.alias_nb_pages()
        self.set_title("MedsAI Diagnostic Report")
        self.set_author("MedsAI System")

        # Typographic rhythm
        self.row_gap = 2.0
        self.line_h = 5.0

    # ---- utilities ----
    def _cw(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def ensure_space(self, needed: float):
        """Prevent orphaned headers/cards at page bottom."""
        if self.get_y() + needed > self.page_break_trigger:
            self.add_page()

    def _nb_lines(self, w: float, txt: str, fs: int) -> int:
        """
        Estimate number of lines MultiCell will use with current font face,
        given width 'w' and font size 'fs'. Keeps alignment consistent.
        """
        if w <= 0:
            return 1
        self.set_font_size(fs)  # ensure correct metrics
        text = safe_str(txt or "")
        # handle explicit line breaks
        lines = 0
        for part in text.split("\n"):
            if not part:
                lines += 1
                continue
            words = part.split(" ")
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                if self.get_string_width(test) <= w:
                    cur = test
                else:
                    lines += 1
                    cur = word
            lines += 1 if cur else 0
        return max(1, lines)

    # ------- aligned label/value row -------
    def kv_row(self, label: str, value: str, lab_w: float = 40, fs: int = 10, draw_line: bool = False):
        """
        A perfectly aligned two-column row:
          [label | value multi-line-wraps] then advances baseline evenly.
        """
        self.ensure_space(12)

        x0, y0 = self.l_margin, self.get_y()
        val_w = self._cw() - lab_w

        # Compute height needed for the value block (lines * line_h)
        self.set_font("Arial", "", fs)
        val_lines = self._nb_lines(val_w, value, fs)
        row_h = max(self.line_h, val_lines * self.line_h)

        # Draw label cell (fixed width, full row height)
        self.set_font("Arial", "B", fs)
        self.set_text_color(*PAL["muted"])
        self.set_xy(x0, y0)
        self.cell(lab_w, row_h, safe_str(label), border=0, align="L")

        # Draw value cell as MultiCell to wrap
        self.set_font("Arial", "", fs)
        self.set_text_color(*PAL["ink"])
        self.set_xy(x0 + lab_w, y0)
        self.multi_cell(val_w, self.line_h, safe_str(value), border=0, align="L")

        # Optionally underline the row for tight tables
        if draw_line:
            self.set_draw_color(*PAL["line"])
            self.line(self.l_margin, y0 + row_h, self.l_margin + self._cw(), y0 + row_h)

        # Move cursor to the end of the row
        self.set_xy(x0, y0 + row_h + self.row_gap)

    # ---- simple bullet list (ASCII only) ----
    def bullet_list(self, items: List[str], indent: float = 3, fs: int = 10):
        self.set_font("Arial", "", fs)
        for it in items or []:
            self.set_x(self.l_margin + indent)
            self.multi_cell(self._cw() - indent, self.line_h, f"- {safe_str(it)}")
        self.ln(self.row_gap)

    # ---- small status chip ----
    def chip(self, text: str):
        self.set_fill_color(*PAL["chip"])
        self.set_draw_color(*PAL["line"])
        self.set_text_color(40, 55, 80)
        self.set_font("Arial", "B", 9)
        w = self.get_string_width(text) + 8
        self.cell(w, 6, text, 1, 0, "C", True)
        self.set_text_color(*PAL["ink"])

    def pct_pill(self, pct: float, risk: str = "HIGH"):
        self.set_font("Arial", "B", 12)
        color = {"HIGH": PAL["bad"], "MEDIUM": PAL["warn"], "LOW": PAL["ok"]}.get(str(risk).upper(), PAL["ok"])
        self.set_text_color(*color)
        self.cell(0, 6, f"{pct_text(pct)} {str(risk).upper()}", 0, 1, "R")
        self.set_text_color(*PAL["ink"])

    # ---- watermark ----
    def _draw_watermark(self):
        cur_x, cur_y = self.get_x(), self.get_y()
        # Title
        self.set_text_color(*PAL["wm_light"])
        self.set_font("Arial", "B", 46)
        wm_text = "MedsAI"
        w = self.get_string_width(wm_text)
        self.set_xy((self.w - w) / 2, self.h * 0.45)
        self.cell(w, 12, wm_text, 0, 1, "C")
        # Subtitle (ASCII only)
        self.set_text_color(*PAL["wm_text"])
        self.set_font("Arial", "", 11)
        sub = "AI-Powered Clinical Decision Support"
        ws = self.get_string_width(sub)
        self.set_x((self.w - ws) / 2)
        self.cell(ws, 6, sub, 0, 1, "C")
        # restore
        self.set_text_color(*PAL["ink"])
        self.set_xy(cur_x, cur_y)

    # ---- header/footer ----
    def header(self):
        # Banner
        self.set_fill_color(*PAL["brand"])
        self.rect(0, 0, self.w, 24, "F")
        self.set_y(5)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 15)
        self.cell(0, 7, "MedsAI Diagnostic Report", 0, 1, "C")
        self.set_font("Arial", "", 9)
        self.cell(0, 5, "Comprehensive AI-Driven Medical Analysis", 0, 1, "C")
        dt = datetime.now().strftime("%B %d, %Y - %I:%M %p")  # ASCII only
        self.cell(0, 5, f"Generated: {dt}", 0, 1, "C")
        self.ln(3)
        # Watermark behind content
        self._draw_watermark()
        self.set_text_color(*PAL["ink"])

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*PAL["line"])
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Arial", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, "Generated by MedsAI Diagnostic System", 0, 1, "C")
        self.set_font("Arial", "", 9)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")
        self.set_text_color(*PAL["ink"])

    # ---- section / card ----
    def section(self, title: str):
        self.ensure_space(20)
        self.set_fill_color(236, 239, 244)
        self.set_draw_color(180, 190, 210)
        y = self.get_y()
        self.rect(self.l_margin, y, self._cw(), 8, "DF")
        self.set_font("Arial", "B", 11)
        self.set_text_color(30, 58, 138)
        self.set_xy(self.l_margin + 2, y + 2)
        self.cell(0, 4, title)
        self.ln(10)
        self.set_text_color(*PAL["ink"])

    def start_card(self):
        self.ensure_space(35)
        self.set_fill_color(*PAL["soft"])
        self.set_draw_color(*PAL["line"])
        y = self.get_y()
        # Border drawn on end (after height is known)
        return y

    def end_card(self, start_y: float, pad: float = 2):
        self.ln(pad)
        end_y = self.get_y()
        self.set_draw_color(*PAL["line"])
        h = max(1, end_y - start_y)
        self.rect(self.l_margin, start_y, self._cw(), h)
        self.ln(1)

    # ---- content blocks ----
    def block_patient(self, data: Dict[str, Any]):
        if not data:
            return
        self.section("Patient Information")
        # Aligned rows (label left, multi-line value right)
        self.kv_row("Patient ID:", safe_str(data.get("patientId", "N/A")), lab_w=40)
        demo = f"Age: {safe_str(data.get('age','N/A'))} | Gender: {safe_str(data.get('gender','N/A')).title()} | Urgency: {safe_str(data.get('urgency','N/A')).upper()}"
        self.kv_row("Demographics:", demo, lab_w=40)
        if data.get("medicalHistory"):
            self.kv_row("Medical History:", safe_str(data.get("medicalHistory")), lab_w=40)
        if data.get("currentMedications"):
            meds = data["currentMedications"]
            meds_list = meds if isinstance(meds, list) else [str(meds)]
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Current Medications", 0, 1)
            self.bullet_list([safe_str(m) for m in meds_list], indent=4, fs=9)
        if data.get("primary_complaint"):
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Primary Complaint", 0, 1)
            self.set_font("Arial", "", 10)
            self.multi_cell(self._cw(), self.line_h, safe_str(data["primary_complaint"]))
            self.ln(self.row_gap)

    def block_agents(self, agents: List[Dict[str, Any]]):
        if not agents:
            return
        self.section("AI Agent Summary")
        # 3 chips per row, aligned
        per_row, gap = 3, 4
        count = 0
        for ag in agents:
            label = f"{ag.get('name','Agent')} {ag.get('status','COMPLETED')} {pct_text(ag.get('progress', 100))}"
            self.chip(label)
            count += 1
            if count % per_row == 0:
                self.ln(8)
            else:
                self.cell(gap, 6, "")
        self.ln(4)

    def block_differential(self, symptom_analysis: Dict[str, Any]):
        if not symptom_analysis:
            return
        self.section("Differential Diagnosis")

        diffs = symptom_analysis.get("top_differentials", [])
        risk = str(symptom_analysis.get("risk_level", "medium")).lower()
        if not diffs:
            self.set_font("Arial", "", 10)
            self.multi_cell(self._cw(), self.line_h, "No differential diagnoses available.")
            return

        # Primary card
        d0 = diffs[0]
        start = self.start_card()
        name = d0.get("name", "Unknown")
        icd = d0.get("icd10cm_code", "N/A")
        rationale = d0.get("rationale", "No rationale provided.")
        conf = {"high": 85, "medium": 70, "low": 50}.get(risk, 70)

        self.set_font("Arial", "B", 11)
        self.cell(0, 6, f"Primary Diagnosis: {name}", 0, 1)
        self.set_font("Arial", "", 9)
        self.cell(0, 5, f"ICD-10: {icd}", 0, 1)
        self.ln(1)
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, "Diagnostic Confidence:", 0, 1)
        self.pct_pill(conf, risk.upper())
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, "Clinical Reasoning:", 0, 1)
        self.set_font("Arial", "", 10)
        self.multi_cell(self._cw(), self.line_h, safe_str(rationale))
        self.end_card(start, 2)

        # Alternatives
        if len(diffs) > 1:
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Alternative Diagnoses to Consider:", 0, 1)
            self.set_font("Arial", "", 9)
            for i, d in enumerate(diffs[1:], 2):
                self.cell(0, 5, f"{i}. {d.get('name','Unknown')} - {d.get('icd10cm_code','N/A')}", 0, 1)
                if d.get("rationale"):
                    self.set_x(self.l_margin + 3)
                    self.multi_cell(self._cw() - 3, 4, safe_str(d["rationale"]))
                    self.ln(1)

    def block_workup(self, primary_dx_name: str):
        self.section("Recommended Diagnostic Workup")
        dx = (primary_dx_name or "").lower()
        if any(k in dx for k in ("diabetes", "gastroparesis")):
            tests = [
                "Fasting Blood Glucose (FBG)",
                "HbA1c (long-term glycemic control)",
                "Gastric emptying study if gastroparesis suspected",
                "Upper GI endoscopy to rule out obstruction",
                "CBC and CMP baseline",
            ]
        elif any(k in dx for k in ("cardiac", "myocardial", "coronary", "acs")):
            tests = [
                "12-lead ECG",
                "High-sensitivity troponin",
                "Chest X-ray",
                "Echocardiogram",
                "Fasting lipid profile",
            ]
        elif any(k in dx for k in ("migraine", "headache")):
            tests = [
                "Focused neurological examination",
                "CT/MRI brain if red flags",
                "Blood pressure trend",
                "Vision assessment",
            ]
        else:
            tests = [
                "CBC, CMP baseline",
                "Urinalysis",
                "Condition-specific imaging/labs per clinical picture",
            ]
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, "Recommended Laboratory & Imaging Studies", 0, 1)
        self.bullet_list(tests, indent=4, fs=9)

    def block_treatment(self, treatment: Dict[str, Any]):
        if not treatment:
            return
        self.section("Treatment Plan")
        items = treatment.get("treatments", [])
        if not items:
            self.set_font("Arial", "", 10)
            self.multi_cell(self._cw(), self.line_h, "No treatment suggestions available.")
            return
        drugs = [t for t in items if t.get("type") == "drug"]
        non = [t for t in items if t.get("type") != "drug"]

        if drugs:
            self.set_font("Arial", "B", 11)
            self.cell(0, 7, "Pharmacological Interventions:", 0, 1)
            for i, t in enumerate(drugs, 1):
                self.set_font("Arial", "B", 10)
                self.cell(0, 6, f"{i}. {t.get('name','-')} ({t.get('class','N/A')})", 0, 1)
                self.set_font("Arial", "", 9)
                if t.get("rationale"):
                    self.set_x(self.l_margin + 3)
                    self.multi_cell(self._cw() - 3, 5, f"Rationale: {safe_str(t['rationale'])}")
                if t.get("source"):
                    self.set_x(self.l_margin + 3)
                    self.set_text_color(100, 100, 100)
                    self.cell(0, 4, f"Source: {safe_str(t['source'])}", 0, 1)
                    self.set_text_color(*PAL["ink"])
                self.ln(1)

        if non:
            self.set_font("Arial", "B", 11)
            self.cell(0, 7, "Lifestyle & Non-Pharmacological Interventions:", 0, 1)
            self.set_font("Arial", "", 9)
            self.bullet_list([f"{t.get('name','-')}: {safe_str(t.get('rationale',''))}".strip(": ")
                               for t in non], indent=4, fs=9)

    def block_literature(self, literature: Dict[str, Any]):
        if not literature:
            return
        self.section("Evidence-Based References")
        arts = literature.get("articles", {})
        summaries = arts.get("summaries", []) if isinstance(arts, dict) else []
        if not summaries:
            self.set_font("Arial", "I", 9)
            self.cell(0, 5, "No relevant literature found for this condition.", 0, 1)
            return
        for i, a in enumerate(summaries[:5], 1):
            self.set_font("Arial", "B", 9)
            self.cell(0, 5, f"[{i}] {safe_str(a.get('title','No title'))}", 0, 1)
            self.set_font("Arial", "", 8)
            self.set_text_color(100, 100, 100)
            pmid = a.get("pmid")
            if pmid:
                self.cell(0, 4, f"PMID: {safe_str(pmid)}", 0, 1)
            self.set_text_color(*PAL["ink"])
            self.set_x(self.l_margin + 3)
            self.set_font("Arial", "", 9)
            self.multi_cell(self._cw() - 3, 4, safe_str(a.get("summary", "")))
            self.ln(2)

    def block_cases(self, case_matcher: Dict[str, Any]):
        if not (case_matcher and case_matcher.get("matched_cases")):
            return
        self.section("Similar Clinical Cases")
        for i, case in enumerate(case_matcher.get("matched_cases", [])[:3], 1):
            self.set_font("Arial", "B", 9)
            self.cell(0, 5, f"{i}. {safe_str(case.get('name','Unknown'))} ({safe_str(case.get('icd_code','N/A'))})", 0, 1)
            self.set_font("Arial", "", 9)
            self.set_x(self.l_margin + 3)
            self.multi_cell(self._cw() - 3, 4, safe_str(case.get("description", "")))
            self.ln(1)

    def block_summary(self, summary: Dict[str, Any]):
        if not summary:
            return
        self.section("Clinical Summary & Next Steps")
        if summary.get("patient_summary"):
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Patient Presentation:", 0, 1)
            self.set_font("Arial", "", 10)
            self.multi_cell(self._cw(), self.line_h, safe_str(summary["patient_summary"]))
            self.ln(1)
        if summary.get("clinical_summary"):
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Clinical Assessment:", 0, 1)
            self.set_font("Arial", "", 10)
            self.multi_cell(self._cw(), self.line_h, safe_str(summary["clinical_summary"]))
            self.ln(1)
        recs = summary.get("recommendations", [])
        next_steps = [r.get("content", "") for r in recs if r.get("type") == "next_steps"]
        if next_steps:
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "Next Steps & Follow-Up", 0, 1)
            self.set_font("Arial", "", 9)
            self.bullet_list([safe_str(s) for s in next_steps], indent=4, fs=9)

# -----------------------------
# Public API (drop-in)
# -----------------------------
def generate_pdf_from_analysis(analysis_data: Dict[str, Any]) -> bytes:
    """
    Build a professional, watermark-styled PDF from your analysis_data dict.
    Keys (all optional except patient_info fields you rely on):
      - patient_info: {patientId, age, gender, urgency, medicalHistory?, currentMedications?, primary_complaint?}
      - agent_summary or agents: [{name, status, progress}, ...]
      - symptom_analysis: {risk_level, top_differentials: [{name, icd10cm_code, rationale}, ...]}
      - treatment: {treatments: [{type:'drug'|'non-drug', name, class?, rationale?, source?}, ...]}
      - literature: {articles: {summaries: [{title, pmid?, summary}, ...]}}
      - case_matcher: {matched_cases: [{name, icd_code, description}, ...]}
      - summary: {patient_summary?, clinical_summary?, recommendations?: [{type:'next_steps', content}, ...]}
    """
    pdf = MedsAIReport()
    pdf.add_page()

    # Patient
    pdf.block_patient(analysis_data.get("patient_info") or {})

    # Agents (chips)
    agents = analysis_data.get("agent_summary") or analysis_data.get("agents") or []
    pdf.block_agents(agents)

    # Differential diagnosis
    symptom = analysis_data.get("symptom_analysis") or {}
    pdf.block_differential(symptom)

    # Workup (use primary dx name if available)
    diffs = symptom.get("top_differentials", []) if isinstance(symptom, dict) else []
    primary_name = diffs[0].get("name") if diffs else ""
    pdf.block_workup(primary_name or "")

    # Treatment
    pdf.block_treatment(analysis_data.get("treatment") or {})

    # Literature
    pdf.block_literature(analysis_data.get("literature") or {})

    # Similar cases
    pdf.block_cases(analysis_data.get("case_matcher") or {})

    # Summary
    pdf.block_summary(analysis_data.get("summary") or {})

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
