"""Shared UI building blocks and visual tokens."""

from __future__ import annotations

from typing import Any

import reflex as rx


FONT_DISPLAY = "'Space Grotesk', 'Avenir Next', sans-serif"
FONT_BODY = "'IBM Plex Sans', 'Helvetica Neue', sans-serif"

SURFACE = "#f4f7f4"
CARD = "rgba(255, 255, 255, 0.86)"
BORDER = "rgba(23, 42, 45, 0.12)"
TEXT_MUTED = "#4f6365"
TEXT_STRONG = "#102325"

SERIES_COLORS = ["#0f766e", "#b45309", "#be123c", "#1d4ed8", "#6d28d9"]


def panel(title: str, description: str, *children: rx.Component) -> rx.Component:
    """Render a section panel with a consistent card treatment."""

    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    title,
                    size="6",
                    font_family=FONT_DISPLAY,
                    color=TEXT_STRONG,
                ),
                rx.text(
                    description,
                    color=TEXT_MUTED,
                    size="3",
                    line_height="1.6",
                ),
                spacing="2",
                align_items="start",
            ),
            *children,
            spacing="5",
            align_items="stretch",
        ),
        background=CARD,
        border=f"1px solid {BORDER}",
        border_radius="24px",
        box_shadow="0 24px 60px rgba(15, 35, 37, 0.08)",
        backdrop_filter="blur(18px)",
        padding="1.5rem",
        width="100%",
    )


def stat_card(
    title: str,
    value: str,
    caption: str,
    accent: str = "#0f766e",
) -> rx.Component:
    """Render a KPI card."""

    return rx.box(
        rx.vstack(
            rx.text(title, size="2", color=TEXT_MUTED, text_transform="uppercase", letter_spacing="0.08em"),
            rx.heading(
                value,
                size="8",
                font_family=FONT_DISPLAY,
                color=TEXT_STRONG,
            ),
            rx.text(caption, size="2", color=TEXT_MUTED),
            spacing="2",
            align_items="start",
        ),
        background=f"linear-gradient(145deg, rgba(255,255,255,0.96), {accent}16)",
        border=f"1px solid {BORDER}",
        border_radius="22px",
        padding="1.25rem",
        min_height="11rem",
        width="100%",
    )


def empty_state(title: str, description: str) -> rx.Component:
    """Render a lightweight empty state."""

    return rx.box(
        rx.vstack(
            rx.heading(title, size="5", font_family=FONT_DISPLAY, color=TEXT_STRONG),
            rx.text(description, size="3", color=TEXT_MUTED, text_align="center"),
            spacing="3",
            align_items="center",
        ),
        background="rgba(255,255,255,0.72)",
        border=f"1px dashed {BORDER}",
        border_radius="18px",
        padding="1.5rem",
    )


def record_select(
    options: list[dict[str, str]],
    value: Any,
    on_change: Any,
    placeholder: str,
) -> rx.Component:
    """Render a select with internal ids and human-friendly labels."""

    return rx.select.root(
        rx.select.trigger(placeholder=placeholder),
        rx.select.content(
            rx.foreach(
                options,
                lambda option: rx.select.item(option["label"], value=option["value"]),
            ),
        ),
        value=value,
        on_change=on_change,
    )
