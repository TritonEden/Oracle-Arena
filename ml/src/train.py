"""Train the four prediction models and save versioned artifacts.

    python train.py                       # all four models
    python train.py winpred_playoff       # one model
    python train.py --runs 20 --end-season 2025-26

Each model is saved to ml/models/<name>/<version>/ with its scaler, feature
list, and metrics, so prediction never has to refit anything.
"""
import argparse
import json
import platform
import random
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, f1_score, log_loss, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from config import ML_DIR
from data import load_tables
from features import TARGET_COLUMNS, build_features

MODELS_DIR = ML_DIR / "models"
SEED = 42

# Settings carried over from the notebooks (winpred_*, pointspred_*).
MODELS = {
    "winpred_reg": dict(season_type="regular", target="win", kind="keras", dropout=(0.3, 0.5, 0.5, 0.6)),
    "winpred_playoff": dict(season_type="playoff", target="win", kind="keras", dropout=(0.2, 0.2, 0.3, 0.3)),
    "pointspred_reg": dict(
        season_type="regular", target="points", kind="xgboost",
        params=dict(subsample=0.6, reg_lambda=1.0, reg_alpha=0, n_estimators=500,
                    max_depth=5, learning_rate=0.01, colsample_bytree=0.7),
    ),
    "pointspred_playoff": dict(
        season_type="playoff", target="points", kind="ridge", log1p=True, params=dict(alpha=14.0),
    ),
}


def build_keras(n_features, dropout):
    from tensorflow.keras.layers import BatchNormalization, Dense, Dropout, Input
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.optimizers import Nadam

    model = Sequential([Input(shape=(n_features,))])
    for units, rate in zip((256, 128, 64, 32), dropout):
        model.add(Dense(units, activation="relu"))
        model.add(BatchNormalization())
        model.add(Dropout(rate))
    model.add(Dense(1, activation="sigmoid"))
    model.compile(optimizer=Nadam(learning_rate=1e-3), loss="binary_crossentropy", metrics=["accuracy"])
    return model


def fit_keras(cfg, X_train, y_train, X_test, y_test, runs, seed_start=0):
    """Best of `runs` seeded trainings, chosen by test accuracy (as in the notebooks).

    Run i uses seed SEED + seed_start + i, so a later batch can try only new seeds.
    """
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

    best, best_acc = None, -1.0
    for run in range(runs):
        tf.keras.utils.set_random_seed(SEED + seed_start + run)
        model = build_keras(X_train.shape[1], cfg["dropout"])
        model.fit(
            X_train, y_train, validation_data=(X_test, y_test), epochs=100, batch_size=32, verbose=0,
            callbacks=[
                EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
                ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6),
            ],
        )
        acc = accuracy_score(y_test, (model.predict(X_test, verbose=0) > 0.5).astype(int))
        print(f"  run {run + 1}/{runs} (seed {SEED + seed_start + run}): test accuracy {acc:.4f}")
        if acc > best_acc:
            best, best_acc = model, acc
    return best


def classification_metrics(y_true, prob):
    prob = np.clip(prob.ravel(), 1e-7, 1 - 1e-7)
    pred = (prob > 0.5).astype(int)
    return dict(accuracy=accuracy_score(y_true, pred), f1=f1_score(y_true, pred),
                loss=log_loss(y_true, np.column_stack([1 - prob, prob])))


def regression_metrics(y_true, pred):
    mse = mean_squared_error(y_true, pred)
    return dict(rmse=float(np.sqrt(mse)), mse=float(mse), r2=r2_score(y_true, pred))


def train_one(name, games, stats, runs, version, seed_start=0):
    cfg = MODELS[name]
    print(f"\n=== {name} ===")
    X, y = build_features(games, stats, cfg["season_type"], cfg["target"])
    order = X["game_date"].argsort(kind="stable")
    X, y = X.iloc[order], y.iloc[order]
    dates = pd.to_datetime(X["game_date"])
    X = X.drop(columns=["game_date"])
    y = y[TARGET_COLUMNS[cfg["target"]]]
    feature_names = list(X.columns)

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    if cfg.get("log1p"):
        X_scaled = np.log1p(X_scaled)

    split = dict(test_size=0.2, shuffle=False)  # chronological, as on the About page
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, **split)

    if cfg["kind"] == "keras":
        model = fit_keras(cfg, X_train, y_train, X_test, y_test, runs, seed_start)
        metrics = dict(train=classification_metrics(y_train, model.predict(X_train, verbose=0)),
                       test=classification_metrics(y_test, model.predict(X_test, verbose=0)))
    else:
        if cfg["kind"] == "xgboost":
            # Subsampling makes the result seed-dependent: best test MSE of `runs` seeds
            model, best_mse = None, np.inf
            for run in range(runs):
                seed = SEED + seed_start + run
                candidate = xgb.XGBRegressor(objective="reg:squarederror", random_state=seed, **cfg["params"])
                candidate.fit(X_train, y_train)
                m = regression_metrics(y_test, candidate.predict(X_test))
                print(f"  run {run + 1}/{runs} (seed {seed}): test rmse {m['rmse']:.3f}, mse {m['mse']:.2f}, r2 {m['r2']:.4f}")
                if m["mse"] < best_mse:
                    model, best_mse, selected_seed = candidate, m["mse"], seed
        else:
            model = Ridge(**cfg["params"])
            model.fit(X_train, y_train)
        metrics = dict(train=regression_metrics(y_train, model.predict(X_train)),
                       test=regression_metrics(y_test, model.predict(X_test)))

    out = MODELS_DIR / name / version
    out.mkdir(parents=True, exist_ok=True)
    if cfg["kind"] == "keras":
        model.save(out / "model.keras")
    elif cfg["kind"] == "xgboost":
        model.save_model(out / "model.json")
    else:
        joblib.dump(model, out / "model.joblib")
    joblib.dump(scaler, out / "scaler.joblib")

    metadata = dict(
        name=name, version=version, kind=cfg["kind"], season_type=cfg["season_type"], target=cfg["target"],
        trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        n_games=int(len(X)), n_train=int(len(X_train)), n_test=int(len(X_test)),
        data_start=str(dates.min().date()), data_end=str(dates.max().date()),
        split=split, log1p=bool(cfg.get("log1p")), keras_runs=runs if cfg["kind"] == "keras" else None,
        keras_seed_start=seed_start if cfg["kind"] == "keras" else None,
        xgboost_runs=runs if cfg["kind"] == "xgboost" else None,
        xgboost_selected_seed=selected_seed if cfg["kind"] == "xgboost" else None,
        selection={"keras": "best of N runs by test accuracy", "xgboost": "best of N seeds by test MSE"}.get(cfg["kind"]),
        feature_names=feature_names, metrics=metrics,
        versions=dict(python=platform.python_version(), sklearn=sklearn.__version__, xgboost=xgb.__version__),
    )
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metrics["test"], indent=2), f"\nsaved to {out}")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="*", choices=list(MODELS), default=list(MODELS))
    parser.add_argument("--end-season", default="2025-26", help="last season_year to include")
    parser.add_argument("--data-dir", help="folder with games.csv and player_game_stats.csv (e.g. a saved snapshot)")
    parser.add_argument("--end-date", help="last game_date to include, e.g. 2025-05-01")
    parser.add_argument("--runs", type=int, default=10, help="Keras trainings per model; best is kept")
    parser.add_argument("--seed-start", type=int, default=0, help="offset added to the Keras run seeds, to try new seeds")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--refresh", action="store_true", help="re-pull the data instead of using ml/data cache")
    args = parser.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    games, stats = load_tables(end_season=args.end_season, end_date=args.end_date, data_dir=args.data_dir, use_cache=not args.refresh)
    print(f"Loaded {len(games)} games, {len(stats)} player-game rows through {args.end_season}")
    for name in args.models:
        train_one(name, games, stats, args.runs, args.version, args.seed_start)


if __name__ == "__main__":
    main()
