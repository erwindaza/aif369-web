"""Search Tool - Query product database"""
import time
from typing import List, Dict, Any, Optional
from tools.base import BaseTool


class SearchTool(BaseTool):
    """
    Search products in database

    Single Responsibility: Search only
    Strategy Pattern: Different search strategies

    Example:
        tool = SearchTool()
        results = await tool.execute(
            query="laptop",
            category="electronics",
            limit=10
        )
    """

    def __init__(self, db_connection: Optional[Any] = None):
        super().__init__(tool_name="search")

        # TODO: Connect to real database (PostgreSQL, SQLite, etc)
        self.db = db_connection
        self._sample_products = [
            {
                "id": "1",
                "title": "Laptop Pro 15",
                "category": "electronics",
                "price": 999.99,
            },
            {
                "id": "2",
                "title": "Mouse Inalámbrico",
                "category": "electronics",
                "price": 29.99,
            },
            {
                "id": "3",
                "title": "Teclado Mecánico",
                "category": "electronics",
                "price": 129.99,
            },
        ]

    async def validate_inputs(self, query: str = "", **kwargs) -> bool:
        """Validate search parameters"""
        if not query or len(query) < 2:
            self.logger.warning(f"Query too short: {query}")
            return False

        limit = kwargs.get("limit", 10)
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            self.logger.warning(f"Invalid limit: {limit}")
            return False

        return True

    async def execute(
        self,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Search products

        Args:
            query: search term
            category: filter by category (optional)
            limit: max results (default 10, max 100)
            **kwargs: additional filters

        Returns:
            {
                "status": "success" | "failed",
                "results": [product1, product2, ...],
                "total_count": int,
                "query_time_ms": float,
                "error": str (optional)
            }
        """
        start_time = time.time()

        # Validate
        if not await self.validate_inputs(query, limit=limit):
            return {
                "status": "failed",
                "results": [],
                "error": "Invalid search parameters",
            }

        try:
            # TODO: Replace with real database query
            # For now: mock search
            results = [p for p in self._sample_products if query.lower() in p["title"].lower()]

            if category:
                results = [p for p in results if p["category"] == category]

            results = results[:limit]

            query_time = (time.time() - start_time) * 1000

            self._execution_count += 1
            self._total_execution_time += query_time

            self.logger.info(
                f"Search '{query}' returned {len(results)} results in {query_time:.0f}ms"
            )

            return {
                "status": "success",
                "results": results,
                "total_count": len(results),
                "query_time_ms": query_time,
            }

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return {
                "status": "failed",
                "results": [],
                "error": str(e),
            }
