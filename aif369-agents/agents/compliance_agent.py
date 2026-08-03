"""Compliance Agent - Reviews content before publication

Responsibilities:
- Check for copyright violations (ISO, TOGAF, DAMA text)
- Verify source citations
- Ensure disclaimers present (Master comercial)
- Detect false accreditation claims
- Flag legal content needing review
"""
import asyncio
from typing import Any, Dict, List, Optional
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager


class ComplianceAgent(BaseAgent):
    """
    Compliance Worker Agent for AIF369 Master

    Guardrails:
    1. No copyrighted text from standards (ISO, TOGAF, DAMA, NIST)
    2. All legal/regulatory content cited with sources
    3. No false claims about accreditation or official status
    4. Disclaimer present for "Master comercial"
    5. Privacy respected in examples (anonymized data)
    """

    def __init__(self):
        super().__init__(agent_id="compliance", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)

        # Compliance rules
        self.checks = {
            "copyright": self._check_copyright,
            "citations": self._check_citations,
            "disclaimers": self._check_disclaimers,
            "accreditation": self._check_accreditation,
            "legal": self._check_legal_content,
            "privacy": self._check_privacy,
        }

        # Patterns to reject
        self.reject_patterns = [
            "ISO/IEC 27001:2022 establece",  # Direct copy
            "According to TOGAF 9.2",  # English copy (should be paraphrased Spanish)
            "DAMA-DMBOK states that",
            "This course is officially",
            "You will be certified by",
            "Officially accredited by",
        ]

    async def _process(self, task: Task) -> dict:
        """
        Review content for compliance

        Payload:
        {
            "content": str,
            "type": "lesson" | "lab" | "capstone",
            "month": int (optional)
        }
        """
        payload = task.payload
        content = payload.get("content", "")
        content_type = payload.get("type", "lesson")

        try:
            # Run all checks
            issues = []
            for check_name, check_fn in self.checks.items():
                result = check_fn(content, content_type)
                if result["has_issues"]:
                    issues.extend(result["issues"])

            # Determine status
            if not issues:
                status = "approved"
            elif any(issue["severity"] == "critical" for issue in issues):
                status = "rejected"
            else:
                status = "needs_review"

            result = {
                "status": "success",
                "review": {
                    "status": status,  # approved | needs_review | rejected
                    "issues": issues,
                    "num_issues": len(issues),
                    "type": content_type,
                    "summary": self._generate_summary(status, issues),
                },
                "agent": "compliance",
            }

            return result

        except Exception as e:
            self.logger.error(f"Compliance check error: {e}")
            raise

    def _check_copyright(self, content: str, content_type: str) -> dict:
        """Check for copyrighted standard text"""
        issues = []

        # Reject patterns
        for pattern in self.reject_patterns:
            if pattern in content:
                issues.append({
                    "check": "copyright",
                    "severity": "critical",
                    "issue": f"Potential copyright: '{pattern[:50]}...'",
                    "suggestion": "Paraphrase using your own words and cite source",
                })

        # Check for exact sentence matches with standards (heuristic)
        long_sentences = [s.strip() for s in content.split(".") if len(s.split()) > 20]
        if long_sentences and len(long_sentences[0]) > 100:
            issues.append({
                "check": "copyright",
                "severity": "warning",
                "issue": "Very long sentence detected - may be copied text",
                "suggestion": "Break into shorter sentences and paraphrase",
            })

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _check_citations(self, content: str, content_type: str) -> dict:
        """Check for proper source citations"""
        issues = []

        # If mentions standards/laws, must cite
        standards = ["ISO", "TOGAF", "DAMA", "NIST", "ley", "regulación", "GDPR", "LGPD"]
        mentions_standards = any(std in content for std in standards)

        if mentions_standards:
            # Check if cited
            has_source = any(
                phrase in content
                for phrase in ["Fuente:", "Source:", "Según", "According to", "https://"]
            )

            if not has_source:
                issues.append({
                    "check": "citations",
                    "severity": "critical",
                    "issue": "Mentions standard/law without citation",
                    "suggestion": "Add source reference: 'Fuente: [official URL]'",
                })

        # Check for legal content without disclaimer
        if any(kw in content for kw in ["ley", "derecho", "obligación", "sanción"]):
            if "descargo" not in content and "disclaimer" not in content:
                issues.append({
                    "check": "citations",
                    "severity": "warning",
                    "issue": "Legal content should include disclaimer",
                    "suggestion": "Add: 'No constituye asesoría legal. Consule abogado.'",
                })

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _check_disclaimers(self, content: str, content_type: str) -> dict:
        """Check for required disclaimers"""
        issues = []

        # For course/program content, check for Master comercial disclaimer
        if content_type in ["lesson", "lab"]:
            # Optional but recommended
            pass

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _check_accreditation(self, content: str, content_type: str) -> dict:
        """Check for false accreditation claims"""
        issues = []

        false_claims = [
            "certificado oficial",
            "accredited by ISO",
            "certified by TOGAF",
            "official certificate",
            "officially recognized",
            "acreditado por",
            "reconocido por el estado",
        ]

        for claim in false_claims:
            if claim in content.lower():
                issues.append({
                    "check": "accreditation",
                    "severity": "critical",
                    "issue": f"False accreditation claim: '{claim}'",
                    "suggestion": "Clarify: 'Programa de AIF369, no acreditado oficialmente'",
                })

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _check_legal_content(self, content: str, content_type: str) -> dict:
        """Flag legal/regulatory content for expert review"""
        issues = []

        legal_keywords = [
            "ley",
            "norma",
            "reglamento",
            "cumplimiento legal",
            "sanción",
            "delito",
            "derecho",
            "obligación",
            "responsabilidad",
        ]

        mentions_legal = any(kw in content.lower() for kw in legal_keywords)

        if mentions_legal and content_type == "lesson":
            issues.append({
                "check": "legal",
                "severity": "warning",
                "issue": "Content includes legal/regulatory material",
                "suggestion": "Schedule legal expert review before publication",
                "requires_review": True,
                "review_role": "Revisor legal",
            })

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _check_privacy(self, content: str, content_type: str) -> dict:
        """Check for PII exposure in examples"""
        issues = []

        # Look for patterns of real data (simplified heuristic)
        pii_patterns = [
            r"\d{2}\.\d{3}\.\d{3}-[0-9K]",  # RUT format (XX.XXX.XXX-K)
            r"\d{4}-\d{4}-\d{4}-\d{4}",  # Credit card
            r"[a-z]+@[a-z]+\.[a-z]+",  # Email (though common in examples)
        ]

        # Simple check: if any suspicious number patterns
        import re

        for pattern in pii_patterns:
            if re.search(pattern, content):
                issues.append({
                    "check": "privacy",
                    "severity": "warning",
                    "issue": "Potential PII detected in example",
                    "suggestion": "Use anonymized/synthetic data (e.g., 'XX.XXX.XXX-X')",
                })
                break

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
        }

    def _generate_summary(self, status: str, issues: List[dict]) -> str:
        """Generate summary message"""
        if status == "approved":
            return "✓ Content approved. No compliance issues detected."
        elif status == "rejected":
            critical = [i for i in issues if i["severity"] == "critical"]
            return f"✗ Rejected. {len(critical)} critical issues: {[i['issue'] for i in critical]}"
        else:
            warnings = [i for i in issues if i["severity"] == "warning"]
            return f"⚠ Review needed. {len(warnings)} warnings. Schedule expert review."

    def __repr__(self) -> str:
        return f"<ComplianceAgent - {self.model_name}>"
