"""Validation Tool - Validate product data"""
import time
import re
from typing import Dict, Any
from tools.base import BaseTool


class ValidationTool(BaseTool):
    """
    Validate product enrichment data

    Single Responsibility: Validation only
    Checks for quality, completeness, correctness

    Example:
        tool = ValidationTool()
        result = await tool.execute(
            title="Laptop Pro 15",
            description="High-performance laptop...",
            keywords=["laptop", "pro", "15-inch"]
        )
    """

    def __init__(self):
        super().__init__(tool_name="validation")

    async def execute(
        self,
        title: str = "",
        description: str = "",
        keywords: list = None,
        price: float = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Validate enriched product data

        Args:
            title: product title
            description: product description
            keywords: SEO keywords
            price: product price
            **kwargs: additional fields

        Returns:
            {
                "status": "valid" | "invalid",
                "score": 0-100,
                "issues": [...],
                "warnings": [...],
                "suggestions": [...]
            }
        """
        start_time = time.time()
        issues = []
        warnings = []
        suggestions = []
        score = 100

        # Validate title
        if not title or len(title) < 5:
            issues.append("Title too short (min 5 chars)")
            score -= 20
        elif len(title) > 200:
            warnings.append("Title longer than recommended (max 200 chars)")
            score -= 5
        else:
            if not re.match(r"^[a-zA-Z0-9\s\-\.áéíóúñ]+$", title):
                warnings.append("Title contains special characters")
                score -= 3

        # Validate description
        if not description or len(description) < 20:
            issues.append("Description too short (min 20 chars)")
            score -= 20
        elif len(description) > 1000:
            warnings.append("Description too long (max 1000 chars)")
            score -= 5
        else:
            if len(description) < 100:
                suggestions.append("Expand description for better SEO (min 100 chars)")
                score -= 5

        # Validate keywords
        if not keywords or len(keywords) == 0:
            warnings.append("No keywords provided")
            score -= 10
        elif len(keywords) > 20:
            warnings.append("Too many keywords (max 20)")
            score -= 5
        else:
            if len(keywords) < 3:
                suggestions.append("Add more keywords (min 3)")
                score -= 5

        # Validate price
        if price is not None:
            if price <= 0:
                issues.append("Price must be positive")
                score -= 15
            elif price > 999999:
                warnings.append("Price seems unusually high")
                score -= 5

        # Final score
        validation_time = (time.time() - start_time) * 1000

        self._execution_count += 1
        self._total_execution_time += validation_time

        status = "valid" if len(issues) == 0 else "invalid"

        self.logger.info(
            f"Validation complete: {status} (score={max(0, score)}, "
            f"issues={len(issues)}, warnings={len(warnings)})"
        )

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "validation_time_ms": validation_time,
        }
