import pandas as pd

from src.report_generator import make_tactical_report


def test_report_shape():
    df = pd.DataFrame(columns=["batter", "bowler"])
    report = make_tactical_report("Unknown Player", "Batter", df, pd.DataFrame())
    assert "strengths" in report
    assert "limitations" in report
