import pandas as pd

from src.metrics import calculate_batter_summary, calculate_bowler_summary, calculate_matchups


def tiny_realistic_frame():
    return pd.DataFrame([
        {"match_id":"1","innings":1,"date":"2024-01-01","match_type":"t20","batting_team":"Team A","bowling_team":"Team B","over":0,"phase":"Powerplay","batter":"Player One","bowler":"Player Two","runs_batter":4,"runs_total":4,"runs_extras":0,"legal_ball":True,"wicket_type":"","player_out":"","is_bowler_wicket":False},
        {"match_id":"1","innings":1,"date":"2024-01-01","match_type":"t20","batting_team":"Team A","bowling_team":"Team B","over":0,"phase":"Powerplay","batter":"Player One","bowler":"Player Two","runs_batter":0,"runs_total":0,"runs_extras":0,"legal_ball":True,"wicket_type":"bowled","player_out":"Player One","is_bowler_wicket":True},
    ])


def test_batter_summary_no_crash():
    out = calculate_batter_summary(tiny_realistic_frame())
    assert not out.empty
    assert "strike_rate" in out.columns


def test_bowler_summary_no_crash():
    out = calculate_bowler_summary(tiny_realistic_frame())
    assert not out.empty
    assert "economy" in out.columns


def test_matchups_no_crash():
    out = calculate_matchups(tiny_realistic_frame())
    assert not out.empty
    assert "risk_score" in out.columns
