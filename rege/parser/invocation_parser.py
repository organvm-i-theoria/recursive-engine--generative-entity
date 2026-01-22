"""
RE:GE Invocation Parser - Parse ritual invocation syntax.

Based on: RE-GE_OS_INTERFACE_01_RITUAL_ACCESS_CO.md

Invocation Syntax:
::CALL_ORGAN [ORGAN_NAME]
::WITH [SYMBOL or INPUT or FRAGMENT]
::MODE [INTENTION_MODE]
::DEPTH [light | standard | full spiral]
::EXPECT [output_form]

Invocation Lifecycle:
INPUT -> PARSE -> VALIDATE -> QUEUE -> EXECUTE -> FORMAT -> LOG
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from rege.core.models import Invocation, DepthLevel


class InvocationParser:
    """
    Parses ritual invocation syntax into structured Invocation objects.

    The parser extracts:
    - ORGAN: Target system organ
    - SYMBOL: Input data/symbol to process
    - MODE: Processing intention mode
    - DEPTH: Recursion depth level
    - EXPECT: Expected output format
    - FLAGS: Special processing flags (ECHO+, FUSE+, etc.)
    """

    # Regex patterns for invocation extraction
    ORGAN_PATTERN = re.compile(r'::CALL_ORGAN\s+(\w+)', re.IGNORECASE)
    WITH_PATTERN = re.compile(r'::WITH\s+["\']?([^"\'\n]+)["\']?', re.IGNORECASE)
    MODE_PATTERN = re.compile(r'::MODE\s+([\w_]+)', re.IGNORECASE)
    DEPTH_PATTERN = re.compile(r'::DEPTH\s+(light|standard|full\s*spiral)', re.IGNORECASE)
    EXPECT_PATTERN = re.compile(r'::EXPECT:?\s+(.+?)(?=::|$)', re.IGNORECASE | re.DOTALL)
    FLAG_PATTERN = re.compile(r'::(\w+\+)', re.IGNORECASE)
    CHARGE_PATTERN = re.compile(r'::CHARGE\s+(\d+)', re.IGNORECASE)

    # Protocol pattern for FUSE01, SYSTEM_RECOVERY, etc.
    PROTOCOL_PATTERN = re.compile(r'::CALL_PROTOCOL\s+(\w+)', re.IGNORECASE)
    OUTPUT_TO_PATTERN = re.compile(r'::OUTPUT_TO\s+(\w+)', re.IGNORECASE)

    def parse(self, text: str) -> Optional[Invocation]:
        """
        Parse invocation text into structured Invocation.

        Args:
            text: Raw invocation text with ritual syntax

        Returns:
            Parsed Invocation object, or None if parsing fails
        """
        # Check for organ call first
        organ = self._extract_organ(text)
        if not organ:
            # Check if this is a protocol call
            protocol = self._extract_protocol(text)
            if protocol:
                organ = f"PROTOCOL_{protocol}"
            else:
                return None

        symbol = self._extract_symbol(text)
        mode = self._extract_mode(text)
        depth = self._extract_depth(text)
        expect = self._extract_expect(text)
        flags = self._extract_flags(text)
        charge = self._extract_charge(text)

        invocation = Invocation(
            organ=organ.upper(),
            symbol=symbol or "",
            mode=mode or "default",
            depth=depth,
            expect=expect or "default_output",
            flags=flags,
            raw_text=text.strip(),
            charge=charge,
        )

        return invocation

    def parse_chain(self, text: str) -> List[Invocation]:
        """
        Parse multiple chained invocations from text.

        Handles advanced usage where multiple organs are called in sequence.

        Args:
            text: Text containing one or more invocations

        Returns:
            List of parsed Invocation objects
        """
        # Split on ::CALL_ORGAN or ::CALL_PROTOCOL but keep delimiter
        segments = re.split(r'(?=::CALL_(?:ORGAN|PROTOCOL))', text, flags=re.IGNORECASE)
        invocations = []

        for segment in segments:
            segment = segment.strip()
            if segment:
                inv = self.parse(segment)
                if inv:
                    invocations.append(inv)

        return invocations

    def _extract_organ(self, text: str) -> Optional[str]:
        """Extract organ name from invocation text."""
        match = self.ORGAN_PATTERN.search(text)
        return match.group(1).upper() if match else None

    def _extract_protocol(self, text: str) -> Optional[str]:
        """Extract protocol name from invocation text."""
        match = self.PROTOCOL_PATTERN.search(text)
        return match.group(1).upper() if match else None

    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract symbol/input from invocation text."""
        match = self.WITH_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_mode(self, text: str) -> Optional[str]:
        """Extract processing mode from invocation text."""
        match = self.MODE_PATTERN.search(text)
        return match.group(1).lower() if match else None

    def _extract_depth(self, text: str) -> DepthLevel:
        """Extract depth level from invocation text."""
        match = self.DEPTH_PATTERN.search(text)
        if match:
            depth_str = match.group(1).lower().strip()
            # Normalize "full spiral" variations
            depth_str = re.sub(r'\s+', ' ', depth_str)
            if depth_str == "light":
                return DepthLevel.LIGHT
            elif depth_str == "full spiral":
                return DepthLevel.FULL_SPIRAL
        return DepthLevel.STANDARD

    def _extract_expect(self, text: str) -> Optional[str]:
        """Extract expected output format from invocation text."""
        match = self.EXPECT_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_flags(self, text: str) -> List[str]:
        """Extract special flags from invocation text."""
        return self.FLAG_PATTERN.findall(text.upper())

    def _extract_charge(self, text: str) -> int:
        """Extract charge value from invocation text (default 50)."""
        match = self.CHARGE_PATTERN.search(text)
        if match:
            charge = int(match.group(1))
            return min(max(charge, 0), 100)  # Clamp to 0-100
        return 50

    def _extract_output_to(self, text: str) -> Optional[str]:
        """Extract output destination for protocol calls."""
        match = self.OUTPUT_TO_PATTERN.search(text)
        return match.group(1).upper() if match else None

    def is_valid_syntax(self, text: str) -> bool:
        """
        Quick check if text contains valid invocation syntax.

        Args:
            text: Text to check

        Returns:
            True if text appears to contain an invocation
        """
        return bool(
            self.ORGAN_PATTERN.search(text) or
            self.PROTOCOL_PATTERN.search(text)
        )

    def extract_fragment_refs(self, text: str) -> List[str]:
        """
        Extract fragment references from invocation text.

        Looks for patterns like:
        - Fragment_v2.6
        - fragment: "name"
        - ["frag1", "frag2"]

        Returns:
            List of fragment identifiers
        """
        refs = []

        # Pattern: Fragment_vX.Y or FragmentName_vX.Y
        version_pattern = re.compile(r'(\w+_v[\d.]+)', re.IGNORECASE)
        refs.extend(version_pattern.findall(text))

        # Pattern: fragment: "name" or Fragment: "name"
        named_pattern = re.compile(r'fragment:\s*["\']([^"\']+)["\']', re.IGNORECASE)
        refs.extend(named_pattern.findall(text))

        # Pattern: ["id1", "id2", ...]
        list_pattern = re.compile(r'\["([^"]+)"(?:,\s*"([^"]+)")*\]')
        for match in list_pattern.finditer(text):
            refs.extend(g for g in match.groups() if g)

        return list(set(refs))  # Deduplicate

    def to_patch_params(self, invocation: Invocation) -> Dict[str, Any]:
        """
        Convert invocation to parameters for creating a Patch.

        Args:
            invocation: Parsed invocation

        Returns:
            Dictionary of parameters for Patch creation
        """
        return {
            "input_node": invocation.symbol or "SELF",
            "output_node": invocation.organ,
            "tags": invocation.flags,
            "charge": invocation.charge,
            "metadata": {
                "invocation_id": invocation.invocation_id,
                "mode": invocation.mode,
                "depth": invocation.depth.value,
                "expect": invocation.expect,
            }
        }


# Convenience function for quick parsing
def parse_invocation(text: str) -> Optional[Invocation]:
    """
    Quick parse of invocation text.

    Args:
        text: Raw invocation text

    Returns:
        Parsed Invocation or None
    """
    parser = InvocationParser()
    return parser.parse(text)


def parse_invocation_chain(text: str) -> List[Invocation]:
    """
    Quick parse of chained invocations.

    Args:
        text: Text containing one or more invocations

    Returns:
        List of parsed Invocations
    """
    parser = InvocationParser()
    return parser.parse_chain(text)
