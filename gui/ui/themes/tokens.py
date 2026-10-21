"""Central color tokens for light and dark themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    name: str
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_secondary: str
    accent: str
    accent_hover: str
    accent_muted: str
    danger: str
    success: str
    warning: str
    nav_bg: str
    nav_hover: str
    nav_active: str
    focus: str
    reader_bg: str
    reader_text: str


LIGHT = ThemeTokens(
    name="light",
    bg="#F5F0E6",
    surface="#FFFCF7",
    surface_alt="#EBE4D6",
    border="#D4CBBA",
    text="#1A1A1A",
    text_secondary="#5C564E",
    accent="#0B5C5C",
    accent_hover="#084848",
    accent_muted="#D5E8E6",
    danger="#B33A3A",
    success="#2F6B4F",
    warning="#C47A1A",
    nav_bg="#EDE6D9",
    nav_hover="#E0D7C6",
    nav_active="#0B5C5C",
    focus="#0B5C5C",
    reader_bg="#FFF9F0",
    reader_text="#1A1A1A",
)

DARK = ThemeTokens(
    name="dark",
    bg="#1A1816",
    surface="#252220",
    surface_alt="#312E2B",
    border="#45403B",
    text="#F2EDE6",
    text_secondary="#A89F94",
    accent="#E07A3D",
    accent_hover="#F08A4D",
    accent_muted="#3A2A20",
    danger="#E07070",
    success="#6AAD7E",
    warning="#E0A050",
    nav_bg="#201E1C",
    nav_hover="#2E2B28",
    nav_active="#E07A3D",
    focus="#E07A3D",
    reader_bg="#1E1C1A",
    reader_text="#F2EDE6",
)
