"""Excel Exporter - Exports reports to Excel."""

from typing import Any, Dict, List
import logging
from io import BytesIO
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exports reports to Excel format."""

    def export_to_excel(
        self, report: Dict[str, Any], file_path: str = None
    ) -> bytes:
        """Export report to Excel."""
        # Create Excel file with pandas
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([{
                "Title": report.get("title"),
                "Generated": report.get("generated_at"),
                "Sections": len(report.get("sections", [])),
            }])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Data sheets for each section
            for idx, section in enumerate(report.get("sections", [])):
                sheet_name = f"Section_{idx+1}"[:31]  # Excel sheet name limit
                if isinstance(section.get("content"), dict):
                    df = pd.DataFrame([section["content"]])
                elif isinstance(section.get("content"), list):
                    df = pd.DataFrame(section["content"])
                else:
                    df = pd.DataFrame([{"data": str(section.get("content"))}])

                df.to_excel(writer, sheet_name=sheet_name, index=False)

        excel_bytes = output.getvalue()

        if file_path:
            with open(file_path, 'wb') as f:
                f.write(excel_bytes)

        return excel_bytes
