"""V1 Agent - Mistral 7B (First Generation - ReAct pattern with tool calling)"""
import asyncio
from typing import Any, Dict, Optional
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager
from tools import WhatsAppTool, SearchTool, ValidationTool, InterAgentEventTool
from core import QueueManager


class V1Agent(BaseAgent):
    """
    Mistral 7B Agent - First Generation
    - Pattern: ReAct (Reasoning + Acting)
    - Speed optimized (7B model, CPU-friendly)
    - Execution time target: <0.5s
    - Tool calling: WhatsApp, Search, Validation, Inter-agent events

    Liskov Substitution: Fully compatible with BaseAgent interface
    Dependency Injection: Tools injected
    """

    def __init__(self):
        super().__init__(agent_id="v1_mistral", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)

        # Initialize tools (Dependency Injection)
        self.whatsapp_tool = WhatsAppTool()
        self.search_tool = SearchTool()
        self.validation_tool = ValidationTool()
        self.queue_manager = QueueManager.get_instance()
        self.inter_agent_tool = InterAgentEventTool(self.queue_manager)

    async def _process(self, task: Task) -> dict:
        """
        Process task using Mistral 7B with tool calling

        ReAct Pattern with Tools:
        1. Thought: Analyze task
        2. Action: Call tools if needed
        3. Observation: Process results
        4. Repeat: Loop until solution

        Tools used:
        - SearchTool: find similar products
        - ValidationTool: validate enrichment
        - WhatsAppTool: notify customer
        - InterAgentTool: request V2 analysis

        Args:
            task: Product enrichment task

        Returns:
            Enrichment suggestions with tool results
        """
        payload = task.payload
        tool_results = {}

        # Extract input
        product_title = payload.get("title", "")
        product_desc = payload.get("description", "")
        product_id = payload.get("product_id")
        customer_phone = payload.get("customer_phone")

        # Build ReAct prompt
        prompt = self._build_react_prompt(product_title, product_desc)

        # Call Mistral 7B
        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.7, "num_predict": 200},
            )

            output_text = response.get("response", "")

            # Parse response into structured format
            suggestions = self._parse_suggestions(output_text)

            # ===== TOOL CALLING =====

            # Tool 1: Search for similar products
            self.logger.debug(f"Calling SearchTool for: {product_title}")
            search_result = await self.search_tool.execute(
                query=product_title, limit=5
            )
            tool_results["search"] = search_result

            # Tool 2: Validate enrichment
            self.logger.debug("Calling ValidationTool")
            validation_result = await self.validation_tool.execute(
                title=suggestions.get("improved_title", product_title),
                description=suggestions.get("improved_description", product_desc),
                keywords=suggestions.get("keywords", []),
            )
            tool_results["validation"] = validation_result

            # Tool 3: If validation score low, request V2 detailed analysis
            if validation_result["score"] < 70:
                self.logger.info("Low validation score, requesting V2 detailed analysis")
                event_result = await self.inter_agent_tool.execute(
                    event_type="request_detailed_analysis",
                    target_agent="v2_llama",
                    data={
                        "product_id": product_id,
                        "title": product_title,
                        "description": product_desc,
                        "initial_suggestions": suggestions,
                    },
                    source_agent="v1_mistral",
                    wait_for_result=False,  # Fire and forget
                )
                tool_results["inter_agent_event"] = event_result

            # Tool 4: Notify customer via WhatsApp
            if customer_phone and validation_result["score"] >= 70:
                self.logger.debug(f"Notifying customer via WhatsApp: {customer_phone}")
                wsp_result = await self.whatsapp_tool.execute(
                    phone=customer_phone,
                    message=f"✅ Tu producto '{product_title}' está siendo enriquecido. "
                    f"Calidad: {validation_result['score']}/100",
                )
                tool_results["whatsapp"] = wsp_result

            return {
                "status": "success",
                "suggestions": suggestions,
                "validation_score": validation_result["score"],
                "tool_results": tool_results,
                "raw_response": output_text,
                "quality_score": 0.75,  # V1 baseline
                "generation": "v1_react",
            }

        except Exception as e:
            self.logger.error(f"Mistral 7B error: {e}")
            raise

    def _build_react_prompt(self, title: str, description: str) -> str:
        """Build ReAct prompt for Mistral"""
        return f"""You are an e-commerce product expert. Analyze the product and suggest improvements.

Product: {title}
Description: {description}

Think step by step:
1. What category does this belong to?
2. What keywords would help discoverability?
3. What improvements would increase sales?
4. What price range is competitive?

Provide concise suggestions in this format:
- CATEGORY: [category]
- KEYWORDS: [keyword1, keyword2, ...]
- IMPROVEMENTS: [improvement1, improvement2]
- SUGGESTED_PRICE: [price_range]
- QUALITY_SCORE: [1-10]"""

    def _parse_suggestions(self, response: str) -> dict:
        """Parse Mistral response into structured format"""
        suggestions = {
            "keywords": [],
            "improvements": [],
            "category": None,
            "price_suggestion": None,
        }

        lines = response.split("\n")

        for line in lines:
            if "CATEGORY:" in line:
                suggestions["category"] = line.split("CATEGORY:")[-1].strip()
            elif "KEYWORDS:" in line:
                kw_str = line.split("KEYWORDS:")[-1].strip()
                suggestions["keywords"] = [k.strip() for k in kw_str.split(",")]
            elif "IMPROVEMENTS:" in line:
                imp_str = line.split("IMPROVEMENTS:")[-1].strip()
                suggestions["improvements"] = [i.strip() for i in imp_str.split(",")]
            elif "SUGGESTED_PRICE:" in line:
                suggestions["price_suggestion"] = (
                    line.split("SUGGESTED_PRICE:")[-1].strip()
                )

        return suggestions

    def __repr__(self) -> str:
        return "<V1Agent mistral:7b ReAct>"
