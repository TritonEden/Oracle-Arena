"""Predict one day's games and write the predictions to the games table.

    python predict.py                          # today's games, from the database
    python predict.py --date 2026-10-22
    python predict.py --date 2026-10-22 --dry-run       # read the DB, write nothing
    python predict.py --date 2026-10-22 --check-write   # run the UPDATE, then roll it back
    python predict.py --date 2025-04-13 --data-dir ../data/snapshot_2025-05-02 --dry-run

Regular-season games (ids starting with 2) use winpred_reg and pointspred_reg; playoff
games (ids starting with 4) use winpred_playoff and pointspred_playoff. Models, scalers and
feature lists come from ml/models/<name>/<version>/; nothing is refit here.

Features for a game only use earlier games, so predict a day whose earlier games are
already played. Further ahead, unplayed games in between make the features approximate.
"""
import argparse
import json
from datetime import date as date_cls

import joblib
import numpy as np
import pandas as pd
import sqlalchemy

from config import ML_DIR, get_database_url
from data import load_tables, query_tables
from features import STATS_COLUMNS, build_features

MODELS_DIR = ML_DIR / "models"

# game-id prefix -> (season_type, win model, points model)
SEASONS = {
    "2": ("regular", "winpred_reg", "pointspred_reg"),
    "4": ("playoff", "winpred_playoff", "pointspred_playoff"),
}

UPDATE_SQL = sqlalchemy.text("""
    UPDATE games AS g
    SET winner = v.winner, total_score_prediction = v.points
    FROM unnest(CAST(:ids AS bigint[]), CAST(:winners AS numeric[]), CAST(:points AS numeric[]))
        AS v(game_id, winner, points)
    WHERE g.game_id = v.game_id
""")


def load_artifact(name, version):
    folder = MODELS_DIR / name / version
    metadata = json.loads((folder / "metadata.json").read_text())
    kind = metadata["kind"]
    if kind == "keras":
        from tensorflow.keras.models import load_model
        model = load_model(folder / "model.keras", compile=False)
    elif kind == "xgboost":
        import xgboost as xgb
        model = xgb.XGBRegressor()
        model.load_model(folder / "model.json")
    else:
        model = joblib.load(folder / "model.joblib")
    return model, joblib.load(folder / "scaler.joblib"), metadata


def run_model(name, version, X):
    """Predict with a saved model; keras returns the home-win probability, the others the total."""
    model, scaler, metadata = load_artifact(name, version)
    columns = metadata["feature_names"]
    if set(columns) != set(X.columns):
        raise SystemExit(f"{name}: features differ from training "
                         f"(missing {sorted(set(columns) - set(X.columns))}, extra {sorted(set(X.columns) - set(columns))})")
    scaled = scaler.transform(X[columns])  # saved scaler, transform only
    if metadata.get("log1p"):
        scaled = np.log1p(scaled)
    if metadata["kind"] == "keras":
        return model.predict(scaled, verbose=0).ravel()
    return model.predict(scaled)


def add_placeholder_stats(day_games, stats):
    """Give each game on the day that has no stats rows a zero-stat row per team.

    Upcoming games may have no player_game_stats rows yet, and features are built from those rows.
    The zeros only create the game's own row; its features use earlier games.
    """
    have = set(stats["game_id"].astype(str))
    missing = day_games[~day_games["game_id"].astype(str).isin(have)]
    rows = []
    for number, game in enumerate(missing.itertuples(index=False), start=1):
        zeros = json.dumps({column: 0 for column in STATS_COLUMNS})
        for team_id, player_id in ((game.home_team_id, -2 * number), (game.away_team_id, -2 * number - 1)):
            rows.append({"game_id": game.game_id, "player_id": player_id, "team_id": team_id,
                         "player_game_stats": zeros})
    return pd.concat([stats, pd.DataFrame(rows)], ignore_index=True) if rows else stats


def predict_day(games, stats, day, version):
    """Return a frame with game_id, winner (1 = home) and total_score_prediction for games on `day`."""
    # Games after `day` can't affect its features; drop them so unplayed future games stay out of the history
    games = games[pd.to_datetime(games["game_date"]) <= day]
    # the DB stores game_id as an integer in games but text in player_game_stats: compare as text
    stats = stats[stats["game_id"].astype(str).isin(games["game_id"].astype(str))]
    day_games = games[pd.to_datetime(games["game_date"]) == day]
    stats = add_placeholder_stats(day_games, stats)
    day_ids = day_games["game_id"].astype(str)
    frames = []
    for prefix, (season_type, win_name, points_name) in SEASONS.items():
        wanted = set(day_ids[day_ids.str.startswith(prefix)])
        if not wanted:
            continue
        # win and points models share the same inputs, so build them once per season type
        X, y = build_features(games, stats, season_type, "win", include_unplayed=True)
        rows = y["game_id"].astype(str).isin(wanted).to_numpy()
        missing = wanted - set(y.loc[rows, "game_id"].astype(str))
        if missing:
            print(f"{season_type}: no features for {sorted(missing)} (a team's first games have no history); skipped")
        if not rows.any():
            continue
        X = X[rows].drop(columns=["game_date"])
        frames.append(pd.DataFrame({
            "game_id": y.loc[rows, "game_id"].astype("int64").to_numpy(),
            "season_type": season_type,
            "home_win_probability": run_model(win_name, version, X),
            "total_score_prediction": run_model(points_name, version, X),
        }))
    if not frames:
        return pd.DataFrame(columns=["game_id", "season_type", "home_win_probability", "winner", "total_score_prediction"])
    out = pd.concat(frames, ignore_index=True)
    out["winner"] = (out["home_win_probability"] > 0.5).astype(int)
    skipped = sorted(set(day_ids) - set(out["game_id"].astype(str)))
    if skipped:
        print(f"not predicted (other game types or no features): {skipped}")
    return out


def write_predictions(predictions, commit=True):
    """Update every game in one statement and one transaction; roll back if any row is missing.

    commit=False runs the same UPDATE and then rolls it back, to test the write without changing data.
    """
    engine = sqlalchemy.create_engine(get_database_url())
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            result = connection.execute(UPDATE_SQL, {
                "ids": [int(g) for g in predictions["game_id"]],
                "winners": [int(w) for w in predictions["winner"]],
                "points": [round(float(p), 2) for p in predictions["total_score_prediction"]],
            })
            if result.rowcount != len(predictions):
                raise RuntimeError(f"expected to update {len(predictions)} games, updated {result.rowcount}; rolled back")
        except Exception:
            transaction.rollback()
            raise
        if commit:
            transaction.commit()
            print(f"Wrote {len(predictions)} predictions to the games table.")
        else:
            transaction.rollback()
            print(f"Check passed: the UPDATE matched {result.rowcount} games. Rolled back; nothing was changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", default=str(date_cls.today()), help="game date, YYYY-MM-DD (default: today)")
    parser.add_argument("--version", default="original", help="artifact folder under ml/models/<name>/")
    parser.add_argument("--data-dir", help="read games.csv + player_game_stats.csv from here instead of the database")
    parser.add_argument("--dry-run", action="store_true", help="print the predictions without writing them")
    parser.add_argument("--check-write", action="store_true",
                        help="run the database UPDATE inside a transaction and roll it back (changes nothing)")
    args = parser.parse_args()

    day = pd.to_datetime(args.date)
    games, stats = load_tables(data_dir=args.data_dir) if args.data_dir else query_tables()
    predictions = predict_day(games, stats, day, args.version)
    if predictions.empty:
        print(f"No games to predict on {args.date}.")
        return
    pd.set_option("display.width", 120)
    print(predictions.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    if args.dry_run or args.data_dir:
        print("Dry run: nothing written." if args.dry_run else "Read from --data-dir: nothing written.")
    else:
        write_predictions(predictions, commit=not args.check_write)


if __name__ == "__main__":
    main()
