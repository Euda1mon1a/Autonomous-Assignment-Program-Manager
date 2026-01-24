"""SQL EXPLAIN plan analyzer for query optimization.

Analyzes PostgreSQL EXPLAIN output to identify performance bottlenecks.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class ExplainMetrics:
    """Metrics from EXPLAIN ANALYZE."""

    total_cost: float
    execution_time_ms: float
    planning_time_ms: float
    rows_returned: int
    rows_scanned: int
    has_sequential_scan: bool
    has_index_scan: bool
    missing_indexes: list[str]
    recommendations: list[str]


class ExplainAnalyzer:
    """Analyzes SQL EXPLAIN plans for optimization opportunities."""

    def __init__(self, session: AsyncSession):
        """Initialize EXPLAIN analyzer.

        Args:
            session: Database session
        """
        self.session = session

    async def analyze_query(
        self,
        query_str: str,
        params: dict[str, Any] | None = None,
        analyze: bool = True,
    ) -> ExplainMetrics:
        """Analyze query execution plan.

        Args:
            query_str: SQL query string
            params: Query parameters
            analyze: If True, run EXPLAIN ANALYZE (actually executes query)

        Returns:
            ExplainMetrics with performance analysis
        """
        # Build EXPLAIN statement
        explain_type = "ANALYZE" if analyze else ""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_str}"

        # Execute EXPLAIN
        result = await self.session.execute(text(explain_query), params or {})
        explain_output = result.scalar()

        # Parse JSON output
        if isinstance(explain_output, str):
            plan_data = json.loads(explain_output)
        else:
            plan_data = explain_output

        # Extract metrics
        return self._parse_plan(plan_data[0])

    def _parse_plan(self, plan_data: dict) -> ExplainMetrics:
        """Parse EXPLAIN JSON output.

        Args:
            plan_data: Parsed JSON plan

        Returns:
            ExplainMetrics with extracted metrics
        """
        plan = plan_data.get("Plan", {})
        execution_time = plan_data.get("Execution Time", 0.0)
        planning_time = plan_data.get("Planning Time", 0.0)

        # Extract node information
        total_cost = plan.get("Total Cost", 0.0)
        rows_returned = plan.get("Actual Rows", 0)
        rows_scanned = self._count_scanned_rows(plan)

        # Detect scan types
        has_seq_scan = self._has_node_type(plan, "Seq Scan")
        has_index_scan = self._has_node_type(plan, "Index Scan")

        # Analyze for recommendations
        missing_indexes = self._identify_missing_indexes(plan)
        recommendations = self._generate_recommendations(
            plan,
            {
                "has_seq_scan": has_seq_scan,
                "total_cost": total_cost,
                "execution_time": execution_time,
            },
        )

        return ExplainMetrics(
            total_cost=total_cost,
            execution_time_ms=execution_time,
            planning_time_ms=planning_time,
            rows_returned=rows_returned,
            rows_scanned=rows_scanned,
            has_sequential_scan=has_seq_scan,
            has_index_scan=has_index_scan,
            missing_indexes=missing_indexes,
            recommendations=recommendations,
        )

    def _has_node_type(self, plan: dict, node_type: str) -> bool:
        """Check if plan contains a specific node type.

        Args:
            plan: Plan node
            node_type: Node type to search for

        Returns:
            True if node type exists in plan
        """
        if plan.get("Node Type") == node_type:
            return True

        # Recursively check children
        for child in plan.get("Plans", []):
            if self._has_node_type(child, node_type):
                return True

        return False

    def _count_scanned_rows(self, plan: dict) -> int:
        """Count total rows scanned across all nodes.

        Args:
            plan: Plan node

        Returns:
            Total rows scanned
        """
        total = plan.get("Actual Rows", 0)

        for child in plan.get("Plans", []):
            total += self._count_scanned_rows(child)

        return int(total)

    def _identify_missing_indexes(self, plan: dict) -> list[str]:
        """Identify potential missing indexes.

        Args:
            plan: Plan node

        Returns:
            List of suggested indexes
        """
        suggestions = []

        # Look for sequential scans with filters
        if plan.get("Node Type") == "Seq Scan":
            table_name = plan.get("Relation Name")
            filter_cond = plan.get("Filter")

            if filter_cond and table_name:
                # Extract column names from filter
                columns = self._extract_filter_columns(filter_cond)
                if columns:
                    index_suggestion = (
                        f"CREATE INDEX idx_{table_name}_"
                        f"{'_'.join(columns)} ON {table_name} "
                        f"({', '.join(columns)});"
                    )
                    suggestions.append(index_suggestion)

        # Recursively check children
        for child in plan.get("Plans", []):
            suggestions.extend(self._identify_missing_indexes(child))

        return suggestions

    def _extract_filter_columns(self, filter_str: str) -> list[str]:
        """Extract column names from filter condition.

        Args:
            filter_str: Filter condition string

        Returns:
            List of column names
        """
        # Simple regex to extract column names
        # This is a basic implementation - could be more sophisticated
        pattern = r"\((\w+)\s+[=<>!]"
        matches = re.findall(pattern, filter_str)
        return list(set(matches))

    def _generate_recommendations(
        self,
        plan: dict,
        metrics: dict,
    ) -> list[str]:
        """Generate optimization recommendations.

        Args:
            plan: Plan node
            metrics: Performance metrics

        Returns:
            List of recommendations
        """
        recommendations = []

        # Sequential scan on large tables
        if metrics["has_seq_scan"] and metrics["total_cost"] > 1000:
            recommendations.append(
                "Consider adding indexes - sequential scans detected on "
                "large tables (cost > 1000)"
            )

        # Slow execution time
        if metrics["execution_time"] > 1000:
            recommendations.append(
                "Query execution time > 1 second - consider optimization or caching"
            )

        # Check for nested loops without indexes
        if self._has_nested_loop_without_index(plan):
            recommendations.append(
                "Nested loop joins detected without index scans - add "
                "indexes on join columns"
            )

        # Check for sorts on large datasets
        if self._has_expensive_sort(plan):
            recommendations.append(
                "Expensive sort operation detected - consider adding "
                "index for ORDER BY columns"
            )

        return recommendations

    def _has_nested_loop_without_index(self, plan: dict) -> bool:
        """Check for nested loops without index scans.

        Args:
            plan: Plan node

        Returns:
            True if nested loop without index detected
        """
        if plan.get("Node Type") == "Nested Loop":
            # Check if any child is a sequential scan
            for child in plan.get("Plans", []):
                if child.get("Node Type") == "Seq Scan":
                    return True

        # Recursively check children
        for child in plan.get("Plans", []):
            if self._has_nested_loop_without_index(child):
                return True

        return False

    def _has_expensive_sort(self, plan: dict) -> bool:
        """Check for expensive sort operations.

        Args:
            plan: Plan node

        Returns:
            True if expensive sort detected
        """
        if plan.get("Node Type") == "Sort":
            # Check if sort is on large dataset
            if plan.get("Actual Rows", 0) > 10000:
                return True

        # Recursively check children
        for child in plan.get("Plans", []):
            if self._has_expensive_sort(child):
                return True

        return False

    async def compare_queries(
        self,
        query1: str,
        query2: str,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Compare performance of two queries.

        Args:
            query1: First query
            query2: Second query
            params: Query parameters

        Returns:
            Comparison results
        """
        metrics1 = await self.analyze_query(query1, params)
        metrics2 = await self.analyze_query(query2, params)

        return {
            "query1": {
                "cost": metrics1.total_cost,
                "execution_time": metrics1.execution_time_ms,
                "rows_scanned": metrics1.rows_scanned,
            },
            "query2": {
                "cost": metrics2.total_cost,
                "execution_time": metrics2.execution_time_ms,
                "rows_scanned": metrics2.rows_scanned,
            },
            "winner": "query1"
            if metrics1.execution_time_ms < metrics2.execution_time_ms
            else "query2",
            "improvement": abs(
                (metrics2.execution_time_ms - metrics1.execution_time_ms)
                / metrics1.execution_time_ms
                * 100
            ),
        }
