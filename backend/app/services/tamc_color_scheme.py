"""
TAMC Color Scheme for Excel Schedule Formatting.

Loads color mappings from TAMC_Color_Scheme_Reference.xml and provides
methods to get colors for schedule codes, headers, and rotation columns.

Central Dogma Pipeline Integration:
    DB → JSON → JSONToXlsxConverter (uses this module) → colored xlsx
    (XML converter remains for validation/legacy tooling.)
"""

from pathlib import Path
from xml.etree import ElementTree

from app.core.logging import get_logger

logger = get_logger(__name__)


# Default path to color scheme XML - check multiple locations
def _find_color_scheme_path() -> Path:
    """Find color scheme XML in either Docker or host directory structure."""
    relative_path = Path("docs/scheduling/TAMC_Color_Scheme_Reference.xml")
    base = Path(__file__).parent.parent.parent  # backend/ or /app

    # Try 3 parents first (Docker: /app)
    docker_path = base / relative_path
    if docker_path.exists():
        return docker_path

    # Try 4 parents (host: project root)
    host_path = base.parent / relative_path
    if host_path.exists():
        return host_path

    # Fallback to Docker path (will log warning if not found)
    return docker_path


DEFAULT_COLOR_SCHEME_PATH = _find_color_scheme_path()


class TAMCColorScheme:
    """
    TAMC color scheme for Excel schedule formatting.

    Parses color scheme XML and provides color lookups for:
    - Schedule codes (C, FMIT, LEC, etc.)
    - Header columns by day of week
    - Rotation column colors
    """

    def __init__(self, xml_path: Path | str | None = None):
        """
        Initialize color scheme from XML file.

        Args:
            xml_path: Path to color scheme XML. Defaults to
                     docs/scheduling/TAMC_Color_Scheme_Reference.xml
        """
        self.xml_path = Path(xml_path) if xml_path else DEFAULT_COLOR_SCHEME_PATH

        # Code → hex color mapping (without leading FF for openpyxl)
        self._code_colors: dict[str, str] = {}

        # Code → font hex color mapping
        self._font_colors: dict[str, str] = {}

        # Header colors by type
        self._header_colors: dict[str, str] = {}

        # Rotation column colors
        self._rotation_colors: dict[str, str] = {}
        self._rotation_mappings: dict[str, str] = {}

        self._load_color_scheme()

    def _load_color_scheme(self) -> None:
        """Load and parse color scheme XML."""
        if not self.xml_path.exists():
            logger.warning(f"Color scheme XML not found: {self.xml_path}")
            return

        try:
            tree = ElementTree.parse(self.xml_path)
            root = tree.getroot()

            # Parse color groups → code mappings
            # Support both flat structure and nested under <fill_colors>
            color_groups = root.findall("color_group")
            if not color_groups:
                color_groups = root.findall(".//fill_colors/color_group")

            for group in color_groups:
                hex_color = group.get("hex_color", "")
                # Remove leading "FF" (alpha channel) for openpyxl
                if hex_color.startswith("FF") and len(hex_color) == 8:
                    hex_color = hex_color[2:]

                for code_elem in group.findall("code"):
                    code = code_elem.get("value", "")
                    if code:
                        self._code_colors[code] = hex_color

            # Parse font colors (text colors with semantic meaning)
            for font_group in root.findall(".//font_colors/font_color_group"):
                hex_color = font_group.get("hex_color", "")
                # Handle theme references (theme:1 → use actual_rgb)
                if hex_color.startswith("theme:"):
                    hex_color = font_group.get("actual_rgb", "FF000000")
                # Remove leading "FF" (alpha channel) for openpyxl
                if hex_color.startswith("FF") and len(hex_color) == 8:
                    hex_color = hex_color[2:]

                for code_elem in font_group.findall("code"):
                    code = code_elem.get("value", "")
                    if code:
                        self._font_colors[code] = hex_color

            # Parse header colors
            for header in root.findall(".//header_colors/header"):
                name = header.get("name", "")
                hex_color = header.get("hex_color", "")
                if hex_color.startswith("FF") and len(hex_color) == 8:
                    hex_color = hex_color[2:]
                if name:
                    self._header_colors[name] = hex_color

            # Parse rotation column colors
            for rotation in root.findall(".//rotation_column_colors/rotation_type"):
                name = rotation.get("name", "")
                hex_color = rotation.get("hex_color", "")
                if hex_color.startswith("FF") and len(hex_color) == 8:
                    hex_color = hex_color[2:]
                if name:
                    self._rotation_colors[name] = hex_color

            # Build rotation name → color type mapping
            self._build_rotation_mappings()

            logger.info(
                f"Loaded color scheme: {len(self._code_colors)} fill codes, "
                f"{len(self._font_colors)} font codes, "
                f"{len(self._header_colors)} headers, "
                f"{len(self._rotation_colors)} rotation types"
            )

        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse color scheme XML: {e}")

    def _build_rotation_mappings(self) -> None:
        """Build rotation name to color type mappings."""
        # Based on rotation_column_colors in XML
        inpatient = ["IM", "Peds Ward", "PedW", "KAP", "LDNF", "L&D", "Surg Exp", "ICU"]
        elective = ["FMC", "NEURO", "SM", "POCUS", "PROC", "Gyn Clinic", "GYN"]
        fmit = ["FMIT", "FMIT 1", "FMIT 2", "FMIT1", "FMIT2"]
        night_float = ["NF", "Peds NF", "PedNF"]
        orientation = ["FMO", "DCC/BOLC/FMO", "DCC", "BOLC"]

        for rot in inpatient:
            self._rotation_mappings[rot] = "inpatient_critical"
        for rot in elective:
            self._rotation_mappings[rot] = "elective_outpatient"
        for rot in fmit:
            self._rotation_mappings[rot] = "fmit"
        for rot in night_float:
            self._rotation_mappings[rot] = "night_float"
        for rot in orientation:
            self._rotation_mappings[rot] = "orientation"

    def get_code_color(self, code: str) -> str | None:
        """
        Get hex color for a schedule code.

        Args:
            code: Schedule code (C, FMIT, LEC, etc.)

        Returns:
            Hex color without alpha (e.g., "FFC000") or None if not found
        """
        return self._code_colors.get(code)

    def get_font_color(self, code: str) -> str | None:
        """
        Get font hex color for a schedule code.

        Font colors have semantic meaning:
        - Red (#FF0000): +1 AT demand (dedicated supervision) - PR, VAS, COLPO, GER
        - Red (#FF0000): Visibility for Lamoureux - HV
        - Light gray (#E8E8E8): Night Float - NF, Peds NF
        - White (#FFFFFF): Contrast on dark backgrounds - HOL, TNG, MM, FED
        - Black (#000000): Default text

        Args:
            code: Schedule code (PR, NF, HOL, etc.)

        Returns:
            Hex color without alpha (e.g., "FF0000") or None if not found
        """
        return self._font_colors.get(code)

    def get_header_color(self, day_of_week: int) -> str | None:
        """
        Get header color based on day of week.

        Args:
            day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday

        Returns:
            Hex color for header background
        """
        # Tuesday (1) and Thursday (3) = light blue
        if day_of_week in (1, 3):
            return self._header_colors.get("tuesday_thursday")
        # Saturday (5) and Sunday (6) = blue-gray
        elif day_of_week in (5, 6):
            return self._header_colors.get("weekend")
        # Other weekdays = white
        else:
            return self._header_colors.get("weekday")

    def get_rotation_color(self, rotation: str) -> str | None:
        """
        Get color for rotation column based on rotation type.

        Args:
            rotation: Rotation name (FMC, FMIT, NF, etc.)

        Returns:
            Hex color for rotation column or None if not found
        """
        color_type = self._rotation_mappings.get(rotation)
        if color_type:
            return self._rotation_colors.get(color_type)
        return None

    @property
    def code_count(self) -> int:
        """Number of codes with color mappings."""
        return len(self._code_colors)


# Module-level singleton for convenience
_color_scheme: TAMCColorScheme | None = None


def get_color_scheme() -> TAMCColorScheme:
    """Get singleton color scheme instance."""
    global _color_scheme
    if _color_scheme is None:
        _color_scheme = TAMCColorScheme()
    return _color_scheme


def get_code_color(code: str) -> str | None:
    """Convenience function to get color for a schedule code."""
    return get_color_scheme().get_code_color(code)


def get_font_color(code: str) -> str | None:
    """Convenience function to get font color for a schedule code."""
    return get_color_scheme().get_font_color(code)


def get_header_color(day_of_week: int) -> str | None:
    """Convenience function to get header color for a day of week."""
    return get_color_scheme().get_header_color(day_of_week)


def get_rotation_color(rotation: str) -> str | None:
    """Convenience function to get color for a rotation."""
    return get_color_scheme().get_rotation_color(rotation)
