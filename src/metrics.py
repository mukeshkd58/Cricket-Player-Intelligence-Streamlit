from __future__ import annotations

import numpy as np
import pandas as pd

from src.feature_engineering import add_derived_delivery_features, bowling_runs, pct, safe_div


def calculate_batter_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_delivery_features(df)
    if df.empty or "batter" not in df.columns:
        return pd.DataFrame()
    legal = df[df["legal_ball"].astype(bool)].copy()
    dismissals = df.loc[df.get("player_out", "").astype(str).eq(df["batter"].astype(str))].groupby("batter").size().rename("dismissals") if "player_out" in df.columns else pd.Series(dtype=int)
    innings = legal.groupby("batter")[["match_id", "innings"]].apply(lambda x: x.drop_duplicates().shape[0]).rename("innings")
    matches = legal.groupby("batter")["match_id"].nunique().rename("matches") if "match_id" in legal.columns else pd.Series(dtype=int)
    g = legal.groupby("batter", dropna=False)
    out = g.agg(
        runs=("runs_batter", "sum"),
        balls=("legal_ball", "sum"),
        dot_balls=("is_dot", "sum"),
        boundaries=("is_boundary", "sum"),
    ).reset_index()
    out = out.merge(dismissals.reset_index(), on="batter", how="left").merge(innings.reset_index(), on="batter", how="left").merge(matches.reset_index(), on="batter", how="left")
    out["dismissals"] = out["dismissals"].fillna(0).astype(int)
    out["innings"] = out["innings"].fillna(0).astype(int)
    out["matches"] = out["matches"].fillna(0).astype(int)
    out["average"] = [round(safe_div(r, d, r), 2) for r, d in zip(out["runs"], out["dismissals"])]
    out["strike_rate"] = [round(safe_div(r * 100, b), 2) for r, b in zip(out["runs"], out["balls"])]
    out["dot_ball_pct"] = [pct(d, b) for d, b in zip(out["dot_balls"], out["balls"])]
    out["boundary_pct"] = [pct(bd, b) for bd, b in zip(out["boundaries"], out["balls"])]
    out["dismissal_rate_pct"] = [pct(d, b) for d, b in zip(out["dismissals"], out["balls"])]
    out["pressure_index"] = (0.55 * out["dot_ball_pct"] + 0.45 * out["dismissal_rate_pct"] * 10).round(2)
    out["weakness_score"] = (0.50 * out["dot_ball_pct"] + 0.35 * out["dismissal_rate_pct"] * 10 + 0.15 * (100 - out["boundary_pct"].clip(0, 100))).round(2)
    out["boundary_risk_score"] = (out["boundary_pct"] * 5).clip(0, 100).round(2)
    out["dismissal_vulnerability_score"] = (out["dismissal_rate_pct"] * 15).clip(0, 100).round(2)
    # consistency from innings runs
    if {"match_id", "innings", "runs_batter"}.issubset(legal.columns):
        per_innings = legal.groupby(["batter", "match_id", "innings"], dropna=False)["runs_batter"].sum().reset_index()
        cv = per_innings.groupby("batter")["runs_batter"].agg(lambda s: float(s.std(ddof=0) / s.mean()) if s.mean() else 1.0).rename("cv")
        out = out.merge(cv.reset_index(), on="batter", how="left")
        out["consistency_score"] = (100 / (1 + out["cv"].fillna(1))).round(2)
        out = out.drop(columns=["cv"])
    else:
        out["consistency_score"] = 0
    # recent form from last five match innings
    if "date" in legal.columns:
        temp = legal.copy()
        temp["date_dt"] = pd.to_datetime(temp["date"], errors="coerce")
        form = temp.groupby(["batter", "match_id", "innings", "date_dt"], dropna=False).agg(runs=("runs_batter", "sum"), balls=("legal_ball", "sum")).reset_index()
        form = form.sort_values(["batter", "date_dt"]).groupby("batter").tail(5)
        recent = form.groupby("batter").apply(lambda x: round(safe_div(x["runs"].sum() * 100, x["balls"].sum()), 2)).rename("recent_form_score")
        dates = temp.groupby("batter")["date_dt"].agg(first_match_date="min", last_match_date="max").reset_index()
        dates["first_match_date"] = dates["first_match_date"].dt.date.astype(str)
        dates["last_match_date"] = dates["last_match_date"].dt.date.astype(str)
        out = out.merge(recent.reset_index(), on="batter", how="left").merge(dates, on="batter", how="left")
    else:
        out["recent_form_score"] = 0
        out["first_match_date"] = ""
        out["last_match_date"] = ""
    return out.sort_values(["runs", "balls"], ascending=False)


def calculate_bowler_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_delivery_features(df)
    if df.empty or "bowler" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["bowling_runs"] = bowling_runs(df)
    legal = df[df["legal_ball"].astype(bool)].copy()
    g = legal.groupby("bowler", dropna=False)
    out = g.agg(
        legal_balls=("legal_ball", "sum"),
        wickets=("is_bowler_wicket", "sum"),
        dot_balls=("is_dot", "sum"),
        boundaries_conceded=("is_boundary", "sum"),
        matches=("match_id", "nunique") if "match_id" in legal.columns else ("legal_ball", "size"),
    ).reset_index()
    runs = df.groupby("bowler")["bowling_runs"].sum().rename("runs_conceded").reset_index()
    innings = legal.groupby("bowler")[["match_id", "innings"]].apply(lambda x: x.drop_duplicates().shape[0]).rename("innings").reset_index() if {"match_id", "innings"}.issubset(legal.columns) else pd.DataFrame({"bowler": out["bowler"], "innings": 0})
    out = out.merge(runs, on="bowler", how="left").merge(innings, on="bowler", how="left")
    out["overs"] = (out["legal_balls"] / 6).round(1)
    out["economy"] = [round(safe_div(r * 6, b), 2) for r, b in zip(out["runs_conceded"], out["legal_balls"])]
    out["average"] = [round(safe_div(r, w, r), 2) for r, w in zip(out["runs_conceded"], out["wickets"])]
    out["strike_rate"] = [round(safe_div(b, w, b), 2) for b, w in zip(out["legal_balls"], out["wickets"])]
    out["dot_ball_pct"] = [pct(d, b) for d, b in zip(out["dot_balls"], out["legal_balls"])]
    out["boundary_conceded_pct"] = [pct(bd, b) for bd, b in zip(out["boundaries_conceded"], out["legal_balls"])]
    out["wicket_rate_pct"] = [pct(w, b) for w, b in zip(out["wickets"], out["legal_balls"])]
    out["threat_score"] = (0.45 * out["dot_ball_pct"] + 0.40 * out["wicket_rate_pct"] * 20 + 0.15 * (100 - out["boundary_conceded_pct"].clip(0, 100))).clip(0, 100).round(2)
    out["boundary_risk_score"] = (out["boundary_conceded_pct"] * 5).clip(0, 100).round(2)
    if "date" in legal.columns:
        dates = pd.to_datetime(legal["date"], errors="coerce")
        temp = legal.assign(date_dt=dates)
        d = temp.groupby("bowler")["date_dt"].agg(first_match_date="min", last_match_date="max").reset_index()
        d["first_match_date"] = d["first_match_date"].dt.date.astype(str)
        d["last_match_date"] = d["last_match_date"].dt.date.astype(str)
        out = out.merge(d, on="bowler", how="left")
    return out.sort_values(["wickets", "legal_balls"], ascending=False)


def calculate_matchups(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_delivery_features(df)
    if df.empty or not {"batter", "bowler"}.issubset(df.columns):
        return pd.DataFrame()
    legal = df[df["legal_ball"].astype(bool)].copy()
    if legal.empty:
        return pd.DataFrame()
    # wicket where this batter is out on this bowler's delivery
    legal["batter_out"] = (legal.get("player_out", "").astype(str) == legal["batter"].astype(str)).astype(int) if "player_out" in legal.columns else 0
    out = legal.groupby(["batter", "bowler"], dropna=False).agg(
        balls=("legal_ball", "sum"),
        runs=("runs_batter", "sum"),
        dismissals=("batter_out", "sum"),
        dot_balls=("is_dot", "sum"),
        boundaries=("is_boundary", "sum"),
        matches=("match_id", "nunique") if "match_id" in legal.columns else ("legal_ball", "size"),
    ).reset_index()
    out["strike_rate"] = [round(safe_div(r * 100, b), 2) for r, b in zip(out["runs"], out["balls"])]
    out["dot_ball_pct"] = [pct(d, b) for d, b in zip(out["dot_balls"], out["balls"])]
    out["boundary_pct"] = [pct(bd, b) for bd, b in zip(out["boundaries"], out["balls"])]
    out["dismissal_rate_pct"] = [pct(d, b) for d, b in zip(out["dismissals"], out["balls"])]
    out["risk_score"] = (0.50 * out["dismissal_rate_pct"] * 12 + 0.30 * out["dot_ball_pct"] + 0.20 * (100 - out["strike_rate"].clip(0, 200) / 2)).clip(0, 100).round(2)
    out["dominance_score"] = (0.55 * (out["strike_rate"].clip(0, 240) / 2.4) + 0.25 * out["boundary_pct"] * 4 + 0.20 * (100 - out["dismissal_rate_pct"] * 15).clip(0, 100)).clip(0, 100).round(2)
    out["matchup_winner"] = np.where(out["dominance_score"] >= out["risk_score"], "Batter", "Bowler")
    return out.sort_values(["balls", "runs"], ascending=False)


def phase_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_delivery_features(df)
    rows = []
    if df.empty or "phase" not in df.columns:
        return pd.DataFrame()
    legal = df[df["legal_ball"].astype(bool)].copy()
    if "batter" in legal.columns:
        tmp = legal.groupby(["batter", "phase"], dropna=False).agg(runs=("runs_batter", "sum"), balls=("legal_ball", "sum"), dots=("is_dot", "sum"), boundaries=("is_boundary", "sum")).reset_index()
        tmp = tmp.rename(columns={"batter": "player"})
        tmp["entity_type"] = "batter"
        tmp["strike_rate"] = [round(safe_div(r * 100, b), 2) for r, b in zip(tmp["runs"], tmp["balls"])]
        tmp["dot_ball_pct"] = [pct(d, b) for d, b in zip(tmp["dots"], tmp["balls"])]
        tmp["boundary_pct"] = [pct(bd, b) for bd, b in zip(tmp["boundaries"], tmp["balls"])]
        rows.append(tmp)
    if "bowler" in legal.columns:
        all_df = df.copy(); all_df["bowling_runs"] = bowling_runs(all_df)
        runs = all_df.groupby(["bowler", "phase"], dropna=False)["bowling_runs"].sum().reset_index()
        tmp = legal.groupby(["bowler", "phase"], dropna=False).agg(balls=("legal_ball", "sum"), wickets=("is_bowler_wicket", "sum"), dots=("is_dot", "sum"), boundaries=("is_boundary", "sum")).reset_index()
        tmp = tmp.merge(runs, on=["bowler", "phase"], how="left")
        tmp = tmp.rename(columns={"bowler": "player", "bowling_runs": "runs"})
        tmp["entity_type"] = "bowler"
        tmp["economy"] = [round(safe_div(r * 6, b), 2) for r, b in zip(tmp["runs"], tmp["balls"])]
        tmp["dot_ball_pct"] = [pct(d, b) for d, b in zip(tmp["dots"], tmp["balls"])]
        tmp["boundary_pct"] = [pct(bd, b) for bd, b in zip(tmp["boundaries"], tmp["balls"])]
        rows.append(tmp)
    return pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()


def venue_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_delivery_features(df)
    if df.empty or "venue" not in df.columns:
        return pd.DataFrame()
    legal = df[df["legal_ball"].astype(bool)].copy()
    rows = []
    if "batter" in legal.columns:
        b = legal.groupby(["batter", "venue"], dropna=False).agg(runs=("runs_batter", "sum"), balls=("legal_ball", "sum"), boundaries=("is_boundary", "sum"), matches=("match_id", "nunique") if "match_id" in legal.columns else ("legal_ball", "size")).reset_index()
        b = b.rename(columns={"batter": "player"}); b["entity_type"] = "batter"; b["strike_rate"] = [round(safe_div(r*100, bl), 2) for r, bl in zip(b["runs"], b["balls"])]
        rows.append(b)
    if "bowler" in legal.columns:
        all_df = df.copy(); all_df["bowling_runs"] = bowling_runs(all_df)
        runs = all_df.groupby(["bowler", "venue"], dropna=False)["bowling_runs"].sum().reset_index()
        bw = legal.groupby(["bowler", "venue"], dropna=False).agg(balls=("legal_ball", "sum"), wickets=("is_bowler_wicket", "sum"), matches=("match_id", "nunique") if "match_id" in legal.columns else ("legal_ball", "size")).reset_index().merge(runs, on=["bowler", "venue"], how="left")
        bw = bw.rename(columns={"bowler": "player", "bowling_runs": "runs"}); bw["entity_type"] = "bowler"; bw["economy"] = [round(safe_div(r*6, bl), 2) for r, bl in zip(bw["runs"], bw["balls"])]
        rows.append(bw)
    return pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()


def batter_strengths_weaknesses(player: str, deliveries: pd.DataFrame, matchups: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    df = add_derived_delivery_features(deliveries)
    player_df = df[df.get("batter", "").astype(str) == player] if not df.empty and "batter" in df.columns else pd.DataFrame()
    strengths, weaknesses, plan = [], [], []
    if player_df.empty:
        return ["Data not available"], ["Data not available"], ["Run the real Cricsheet pipeline with enough deliveries for this player."]
    legal = player_df[player_df["legal_ball"].astype(bool)]
    balls = int(legal.shape[0])
    runs = int(legal["runs_batter"].sum())
    sr = safe_div(runs * 100, balls)
    dot = pct(legal["is_dot"].sum(), balls)
    boundary = pct(legal["is_boundary"].sum(), balls)
    dism = int((player_df.get("player_out", "").astype(str) == player).sum()) if "player_out" in player_df.columns else 0
    dism_rate = pct(dism, balls)
    if sr >= 135:
        strengths.append(f"High scoring tempo: strike rate {sr:.1f} across {balls} balls.")
    if boundary >= 16:
        strengths.append(f"Boundary pressure: {boundary:.1f}% of legal balls become fours/sixes.")
    if dism_rate <= 2 and balls >= 100:
        strengths.append(f"Low dismissal frequency: {dism_rate:.1f}% of balls result in dismissal.")
    if dot >= 42:
        weaknesses.append(f"Dot-ball build-up risk: dot-ball percentage is {dot:.1f}%.")
    if sr < 105 and balls >= 60:
        weaknesses.append(f"Scoring-rate concern: strike rate is only {sr:.1f}.")
    if dism_rate >= 4:
        weaknesses.append(f"Dismissal vulnerability: dismissal rate is {dism_rate:.1f}% per legal ball.")
    if "phase" in legal.columns:
        phase = legal.groupby("phase").agg(runs=("runs_batter", "sum"), balls=("legal_ball", "sum"), dots=("is_dot", "sum")).reset_index()
        phase["sr"] = [safe_div(r*100,b) for r,b in zip(phase.runs, phase.balls)]
        phase["dot"] = [pct(d,b) for d,b in zip(phase.dots, phase.balls)]
        phase = phase[phase["balls"] >= 12]
        if not phase.empty:
            best = phase.sort_values("sr", ascending=False).iloc[0]
            worst = phase.sort_values("sr", ascending=True).iloc[0]
            strengths.append(f"Best phase: {best.phase} scoring at {best.sr:.1f} SR.")
            weaknesses.append(f"Watch phase: {worst.phase} scoring at {worst.sr:.1f} SR.")
            plan.append(f"Opposition should attack in {worst.phase}; batter should pre-plan rotation options there.")
    if not matchups.empty and "batter" in matchups.columns:
        pm = matchups[(matchups["batter"].astype(str) == player) & (matchups["balls"] >= 12)]
        if not pm.empty:
            trouble = pm.sort_values("risk_score", ascending=False).head(3)
            trouble_names = ", ".join(trouble["bowler"].astype(str).tolist())
            weaknesses.append(f"Trouble matchups by risk score: {trouble_names}.")
            plan.append(f"Use bowlers with similar profiles to {trouble_names}; protect release shots early in the spell.")
    if not strengths:
        strengths.append("No strong positive pattern yet; sample may be small or performance is mixed.")
    if not weaknesses:
        weaknesses.append("No major statistical weakness detected from available deliveries.")
    if not plan:
        plan.append("Build innings with early strike rotation, avoid dot-ball clusters, and target favorable matchups only after set phase.")
    return strengths, weaknesses, plan


def bowler_strengths_weaknesses(player: str, deliveries: pd.DataFrame, matchups: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    df = add_derived_delivery_features(deliveries)
    player_df = df[df.get("bowler", "").astype(str) == player] if not df.empty and "bowler" in df.columns else pd.DataFrame()
    strengths, weaknesses, plan = [], [], []
    if player_df.empty:
        return ["Data not available"], ["Data not available"], ["Run the real Cricsheet pipeline with enough deliveries for this player."]
    player_df = player_df.copy(); player_df["bowling_runs"] = bowling_runs(player_df)
    legal = player_df[player_df["legal_ball"].astype(bool)]
    balls = int(legal.shape[0])
    runs = float(player_df["bowling_runs"].sum())
    wkts = int(legal["is_bowler_wicket"].sum())
    eco = safe_div(runs*6, balls)
    dot = pct(legal["is_dot"].sum(), balls)
    boundary = pct(legal["is_boundary"].sum(), balls)
    w_rate = pct(wkts, balls)
    if eco <= 7.2:
        strengths.append(f"Run control: economy {eco:.2f} across {balls/6:.1f} overs.")
    if dot >= 38:
        strengths.append(f"Pressure creation: dot-ball percentage {dot:.1f}%.")
    if w_rate >= 4:
        strengths.append(f"Wicket threat: wicket rate {w_rate:.1f}% per legal ball.")
    if eco >= 9:
        weaknesses.append(f"Economy leakage: economy {eco:.2f}.")
    if boundary >= 14:
        weaknesses.append(f"Boundary risk: boundary conceded percentage {boundary:.1f}%.")
    if w_rate < 2 and balls >= 60:
        weaknesses.append(f"Low strike threat: wicket rate only {w_rate:.1f}% per legal ball.")
    if "phase" in legal.columns:
        phase = legal.groupby("phase").agg(balls=("legal_ball", "sum"), wickets=("is_bowler_wicket", "sum"), dots=("is_dot", "sum"), boundaries=("is_boundary", "sum")).reset_index()
        all_runs = player_df.groupby("phase")["bowling_runs"].sum().reset_index()
        phase = phase.merge(all_runs, on="phase", how="left")
        phase["eco"] = [safe_div(r*6,b) for r,b in zip(phase.bowling_runs, phase.balls)]
        phase = phase[phase["balls"] >= 12]
        if not phase.empty:
            best = phase.sort_values("eco").iloc[0]
            worst = phase.sort_values("eco", ascending=False).iloc[0]
            strengths.append(f"Best control phase: {best.phase} economy {best.eco:.2f}.")
            weaknesses.append(f"Weak phase: {worst.phase} economy {worst.eco:.2f}.")
            plan.append(f"Use this bowler more in {best.phase}; add protection/variation plan in {worst.phase}.")
    if not matchups.empty and "bowler" in matchups.columns:
        pm = matchups[(matchups["bowler"].astype(str) == player) & (matchups["balls"] >= 12)]
        if not pm.empty:
            best = pm.sort_values("risk_score", ascending=False).head(3)
            exposed = pm.sort_values("dominance_score", ascending=False).head(3)
            strengths.append("Dominates matchups: " + ", ".join(best["batter"].astype(str).tolist()) + ".")
            weaknesses.append("Can be attacked by: " + ", ".join(exposed["batter"].astype(str).tolist()) + ".")
    if not strengths:
        strengths.append("No standout bowling strength detected yet; sample may be small or mixed.")
    if not weaknesses:
        weaknesses.append("No major statistical weakness detected from available deliveries.")
    if not plan:
        plan.append("Maintain dot-ball pressure, avoid predictable boundary balls, and use matchup-specific fields.")
    return strengths, weaknesses, plan
