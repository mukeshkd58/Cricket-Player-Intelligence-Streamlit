from __future__ import annotations

import html
import re
from typing import Any

import pandas as pd
import streamlit as st

from src.data_loader import load_player_image_map


def normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", str(name).strip()) if p]
    if not parts:
        return "🏏"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@st.cache_data(show_spinner=False)
def _image_map_cached() -> pd.DataFrame:
    return load_player_image_map()


def get_player_image(player_name: str) -> dict[str, str] | None:
    img_df = _image_map_cached()
    if img_df.empty or "player" not in img_df.columns or "image_url" not in img_df.columns:
        return None
    key = normalise(player_name)
    candidates = img_df[img_df["player"].map(normalise) == key]
    if candidates.empty:
        return None
    row = candidates.iloc[0].fillna("")
    url = str(row.get("image_url", "")).strip()
    if not url:
        return None
    return {
        "url": url,
        "source": str(row.get("image_source", "Wikimedia Commons")).strip(),
        "credit": str(row.get("credit", "Attribution unavailable; review Commons metadata")).strip(),
    }


def render_player_card(player: str, meta: str, stats: list[tuple[str, str]], image_note: bool = True) -> None:
    img = get_player_image(player)
    init = html.escape(initials(player))
    safe_name = html.escape(player)
    safe_meta = html.escape(meta or "Data not available")
    if img:
        safe_url = html.escape(img["url"], quote=True)
        avatar = f'<img class="player-avatar" src="{safe_url}" alt="{safe_name} image" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';"/><div class="player-avatar-fallback" style="display:none;">{init}</div>'
        image_line = f"Real image source: {html.escape(img.get('source',''))}. Credit: {html.escape(img.get('credit',''))}"
    else:
        avatar = f'<div class="player-avatar-fallback">{init}</div>'
        image_line = "Player image unavailable — professional silhouette/initials fallback shown."
    stat_html = "".join(
        f"<div><div class='metric-label'>{html.escape(label)}</div><div style='font-weight:900;font-size:1.05rem;color:#fff'>{html.escape(str(value))}</div></div>"
        for label, value in stats
    )
    st.markdown(
        f"""
        <div class="player-card">
          <div class="player-card-head">
            {avatar}
            <div>
              <div class="player-name">{safe_name}</div>
              <div class="player-meta">{safe_meta}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.75rem;margin-top:1rem;">
            {stat_html}
          </div>
          {f'<div class="small-note" style="margin-top:.7rem;">{html.escape(image_line)}</div>' if image_note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
