"""
Model comparison, evaluation charts, and an offline-ready HTML report.
"""

import base64
import html
import json
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


MODEL_COLORS = {
    "Linear Regression": "#64748b",
    "Random Forest": "#0f766e",
    "XGBoost": "#2563eb",
    "DNN": "#9333ea",
}


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calculates MAE, RMSE, MAPE, and R2 score."""
    y_pred = np.clip(y_pred, a_min=0, a_max=None)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    non_zero_mask = y_true > 0
    if np.sum(non_zero_mask) > 0:
        mape = np.mean(
            np.abs(
                (y_true[non_zero_mask] - y_pred[non_zero_mask])
                / y_true[non_zero_mask]
            )
        ) * 100
    else:
        mape = 0.0

    return {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "MAPE (%)": round(float(mape), 2),
        "R2_Score": round(float(r2), 4),
    }


def _save_metric_chart(comparison_df: pd.DataFrame, output_path: str) -> None:
    metrics = [
        ("MAE", "MAE (bikes)", "Lower is better"),
        ("RMSE", "RMSE (bikes)", "Lower is better"),
        ("MAPE (%)", "MAPE (%)", "Lower is better*"),
        ("R2_Score", "R² score", "Higher is better"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    for axis, (column, title, direction) in zip(axes.flat, metrics):
        ordered = comparison_df.sort_values(
            column, ascending=column != "R2_Score"
        )
        bars = axis.bar(
            ordered["Model"],
            ordered[column],
            color=[MODEL_COLORS.get(name, "#475569") for name in ordered["Model"]],
        )
        axis.set_title(f"{title} — {direction}", loc="left", fontweight="bold")
        axis.set_ylabel(title)
        axis.tick_params(axis="x", rotation=18)
        axis.grid(axis="y", alpha=0.2)
        axis.bar_label(bars, fmt="%.3g", padding=3, fontsize=8)

    fig.suptitle("Holdout performance comparison", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _save_prediction_chart(
    y_true: np.ndarray, predictions: dict, output_path: str
    ) -> None:
    count = len(predictions)
    columns = 2
    rows = (count + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(13, 5 * rows), squeeze=False)
    lower = min(float(np.min(y_true)), min(float(np.min(p)) for p in predictions.values()))
    upper = max(float(np.max(y_true)), max(float(np.max(p)) for p in predictions.values()))

    for axis, (name, y_pred) in zip(axes.flat, predictions.items()):
        axis.scatter(y_true, y_pred, s=13, alpha=0.35, color=MODEL_COLORS.get(name))
        axis.plot([lower, upper], [lower, upper], "--", color="#dc2626", linewidth=1.5)
        axis.set_title(name, loc="left", fontweight="bold")
        axis.set_xlabel("Actual demand (bikes)")
        axis.set_ylabel("Predicted demand (bikes)")
        axis.grid(alpha=0.2)

    for axis in axes.flat[count:]:
        axis.set_visible(False)
    fig.suptitle("Actual vs predicted demand (holdout)", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _save_residual_chart(
    y_true: np.ndarray, predictions: dict, output_path: str
    ) -> None:
    count = len(predictions)
    columns = 2
    rows = (count + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(13, 4.5 * rows), squeeze=False)

    for axis, (name, y_pred) in zip(axes.flat, predictions.items()):
        residuals = y_true - y_pred
        axis.hist(
            residuals,
            bins=35,
            color=MODEL_COLORS.get(name),
            alpha=0.82,
            edgecolor="white",
        )
        axis.axvline(0, color="#dc2626", linestyle="--", linewidth=1.5)
        axis.set_title(name, loc="left", fontweight="bold")
        axis.set_xlabel("Residual = actual − predicted (bikes)")
        axis.set_ylabel("Number of observations")
        axis.grid(axis="y", alpha=0.2)

    for axis in axes.flat[count:]:
        axis.set_visible(False)
    fig.suptitle("Prediction error distribution (holdout)", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _feature_scores(model, feature_names: list) -> dict:
    if hasattr(model, "coef_"):
        scores = np.abs(np.asarray(model.coef_).reshape(-1))
    elif hasattr(model, "feature_importances_"):
        scores = np.asarray(model.feature_importances_).reshape(-1)
    elif hasattr(model, "get_booster"):
        raw_scores = model.get_booster().get_score(importance_type="gain")
        scores = np.zeros(len(feature_names), dtype=float)
        for index, name in enumerate(feature_names):
            scores[index] = raw_scores.get(name, raw_scores.get(f"f{index}", 0.0))
    else:
        return {}

    if len(scores) != len(feature_names):
        return {}
    return dict(zip(feature_names, scores.astype(float)))


def _save_feature_chart(
    models_dict: dict, feature_names: list, output_path: str
    ) -> None:
    available = [
        (name, _feature_scores(model, feature_names))
        for name, model in models_dict.items()
    ]
    available = [(name, scores) for name, scores in available if scores]
    columns = 2
    rows = max(1, (len(available) + columns - 1) // columns)
    fig, axes = plt.subplots(rows, columns, figsize=(14, 5 * rows), squeeze=False)

    for axis, (name, scores) in zip(axes.flat, available):
        scale = max(scores.values()) or 1.0
        top = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:12]
        labels, values = zip(*reversed(top))
        axis.barh(
            labels,
            [value / scale for value in values],
            color=MODEL_COLORS.get(name, "#475569"),
        )
        axis.set_xlim(0, 1.08)
        axis.set_xlabel("Relative importance (scaled within this model)")
        axis.set_title(name, loc="left", fontweight="bold")
        axis.grid(axis="x", alpha=0.2)

    for axis in axes.flat[len(available):]:
        axis.set_visible(False)
    fig.suptitle(
        "Feature relevance (model-specific; not directly comparable)",
        fontsize=15,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _save_training_chart(training_history: dict, output_path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    dnn_history = training_history.get("DNN", {})
    dnn_loss = dnn_history.get("loss", [])
    dnn_val_loss = dnn_history.get("val_loss", [])

    if dnn_loss:
        epochs = np.arange(1, len(dnn_loss) + 1)
        axes[0].plot(epochs, dnn_loss, label="Training MSE", color=MODEL_COLORS["DNN"])
        if dnn_val_loss:
            axes[0].plot(
                np.arange(1, len(dnn_val_loss) + 1),
                dnn_val_loss,
                label="Validation MSE",
                color="#f97316",
            )
        axes[0].set_title("DNN — MSE loss by epoch", loc="left", fontweight="bold")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Mean squared error (bikes²)")
        axes[0].legend()
        axes[0].grid(alpha=0.2)
    else:
        axes[0].text(
            0.5,
            0.5,
            "DNN training history was not captured.",
            ha="center",
            va="center",
            transform=axes[0].transAxes,
        )
        axes[0].set_axis_off()

    xgb_history = training_history.get("XGBoost", {})
    validation = xgb_history.get("validation_0", {})
    xgb_rmse = validation.get("rmse", [])
    if xgb_rmse:
        axes[1].plot(
            np.arange(1, len(xgb_rmse) + 1),
            xgb_rmse,
            color=MODEL_COLORS["XGBoost"],
        )
        axes[1].set_title(
            "XGBoost — validation RMSE by boosting round",
            loc="left",
            fontweight="bold",
        )
        axes[1].set_xlabel("Boosting round")
        axes[1].set_ylabel("Validation RMSE (bikes)")
        axes[1].grid(alpha=0.2)
    else:
        axes[1].text(
            0.5,
            0.5,
            "XGBoost validation history was not captured.",
            ha="center",
            va="center",
            transform=axes[1].transAxes,
        )
        axes[1].set_axis_off()

    fig.suptitle("Training objectives and convergence", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _image_data_uri(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _write_html_report(
    comparison_df: pd.DataFrame,
    chart_paths: dict,
    sample_count: int,
    report_path: str,
) -> None:
    best_model = comparison_df.sort_values(
        ["RMSE", "R2_Score"], ascending=[True, False]
    ).iloc[0]
    rows = []
    for _, row in comparison_df.iterrows():
        rows.append(
            "<tr>"
            f"<th scope='row'>{html.escape(str(row['Model']))}</th>"
            f"<td>{row['MAE']:.4f}</td><td>{row['RMSE']:.4f}</td>"
            f"<td>{row['MAPE (%)']:.2f}%</td><td>{row['R2_Score']:.4f}</td>"
            "</tr>"
        )

    chart_titles = {
        "metrics": "Measurement parameters",
        "predictions": "Actual demand vs model prediction",
        "residuals": "Residual / error distribution",
        "training": "Loss and validation learning curves",
        "features": "Feature relevance and XGBoost gain",
    }
    chart_sections = []
    for key, title in chart_titles.items():
        chart_sections.append(
            f"<section><h2>{title}</h2>"
            f"<img alt='{html.escape(title)}' src='{_image_data_uri(chart_paths[key])}'>"
            "</section>"
        )

    report = f"""<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Bike Demand — Model Evaluation</title>
<style>
body{{font-family:Arial,"Noto Sans Bengali",sans-serif;line-height:1.65;color:#172033;background:#f4f7fb;margin:0}}
main{{max-width:1120px;margin:32px auto;padding:0 20px}}
header,.card,section{{background:#fff;border:1px solid #dfe6ef;border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 3px 14px #1720330b}}
h1{{margin-top:0}}h2{{font-size:1.2rem;margin-top:0}}img{{display:block;width:100%;height:auto}}
.winner{{border-left:5px solid #16a34a}}.muted{{color:#526174}}
table{{border-collapse:collapse;width:100%;font-size:.95rem}}th,td{{padding:10px;text-align:right;border-bottom:1px solid #e5eaf1}}
th:first-child,td:first-child{{text-align:left}}thead{{background:#eef3f8}}
code{{background:#eef3f8;padding:2px 5px;border-radius:4px}}footer{{padding:12px 0 36px;color:#526174}}
@media(max-width:680px){{main{{margin:12px auto;padding:0 10px}}header,.card,section{{padding:14px}}table{{font-size:.8rem}}th,td{{padding:7px 4px}}}}
</style>
</head>
<body><main>
<header><h1>Smart Bike Demand — Model Evaluation</h1>
<p>একই holdout data-তে চারটি demand prediction model-এর ফলাফল, error, loss এবং feature গুরুত্ব।</p>
<p class="muted">পরীক্ষিত holdout observation: {sample_count:,}। চার্টগুলো এই HTML ফাইলেই যুক্ত; ইন্টারনেট ছাড়াই খুলবে।</p>
</header>
<div class="card winner"><h2>সেরা ফল (RMSE অনুযায়ী)</h2>
<p><strong>{html.escape(str(best_model['Model']))}</strong> — RMSE {best_model['RMSE']:.4f}, MAE {best_model['MAE']:.4f}, R² {best_model['R2_Score']:.4f}।
কম RMSE মানে বড় prediction error কম; R² 1-এর কাছাকাছি হলে demand variation ভালো ব্যাখ্যা হয়।</p></div>
<section><h2>মডেল তুলনার পরিমাপ</h2>
<table><thead><tr><th>Model</th><th>MAE ↓</th><th>RMSE ↓</th><th>MAPE ↓</th><th>R² ↑</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="muted">MAE/RMSE-এর একক bike। MAPE শূন্য actual demand বাদ দিয়ে হিসাব করা; খুব কম actual demand-এ এটি তুলনামূলক বেশি হতে পারে।</p></section>
<section class="card"><h2>কোন মডেল কেন ভালো?</h2>
<ul>
<li><strong>Linear Regression:</strong> ordinary least squares-এ squared residual-এর যোগফল (RSS) কমায়। সহজে ব্যাখ্যা করা যায়, তবে জটিল non-linear demand pattern ধরতে সীমাবদ্ধ।</li>
<li><strong>Random Forest:</strong> প্রতিটি tree-তে <code>squared_error</code> split criterion ব্যবহার করে এবং বহু tree-এর prediction গড় করে। এটি epoch-ভিত্তিক global loss curve শেখে না।</li>
<li><strong>XGBoost:</strong> <code>reg:squarederror</code> objective দিয়ে আগের tree-এর error সংশোধন করে boosting করে; validation RMSE কমা ভালো। <em>Gain</em> হলো feature-টির split-গুলোতে গড় loss reduction—বেশি gain মানে ঐ feature split-এ বেশি অবদান রেখেছে।</li>
<li><strong>DNN:</strong> Adam optimizer দিয়ে <code>MSE = mean((actual − predicted)²)</code> loss কমায়; training ও validation curve-এর ব্যবধান overfitting বোঝাতে সাহায্য করে। MAE আলাদা evaluation metric হিসেবে দেখানো হয়েছে।</li>
</ul>
<p>Loss/learning curve কেবল iterative model-এর জন্য দেখানো হয়েছে: DNN-এর MSE এবং XGBoost-এর validation RMSE। Linear Regression ও Random Forest-এর জন্য কৃত্রিম epoch-loss curve দেখানো হয়নি।</p>
<p>Feature chart-এ Linear Regression-এর absolute coefficient, Random Forest-এর impurity importance এবং XGBoost-এর average gain দেখানো হয়েছে। এগুলোর scale মডেলভেদে আলাদা—একটির মানের সাথে অন্যটির সরাসরি তুলনা নয়। DNN-এর native feature gain নেই, তাই সেটি এখানে দেখানো হয়নি।</p>
</section>
{''.join(chart_sections)}
<footer>Evaluation data: chronological 80/20 split of the cleaned training dataset. Predictions are clipped at zero before metrics, consistently with the evaluation code.</footer>
</main></body></html>"""

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report)


def evaluate_and_compare_models(
    models_dict: dict,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    reports_dir: str = "ml_engine/reports",
    training_history: dict = None,
    ) -> pd.DataFrame:
    """Evaluate models and write metrics, charts, and a standalone HTML report."""
    os.makedirs(reports_dir, exist_ok=True)
    chart_dir = os.path.join(reports_dir, "figures")
    os.makedirs(chart_dir, exist_ok=True)

    y_true = np.asarray(y_test).reshape(-1)
    results = []
    predictions = {}
    for name, model in models_dict.items():
        y_pred = np.asarray(model.predict(X_test)).reshape(-1)
        y_pred = np.clip(y_pred, a_min=0, a_max=None)
        metrics = calculate_metrics(y_true, y_pred)
        metrics["Model"] = name
        results.append(metrics)
        predictions[name] = y_pred

    comparison_df = pd.DataFrame(results)[
        ["Model", "MAE", "RMSE", "MAPE (%)", "R2_Score"]
    ]
    comparison_df = comparison_df.sort_values(by="RMSE", ascending=True).reset_index(drop=True)

    json_path = os.path.join(reports_dir, "model_comparison.json")
    with open(json_path, "w", encoding="utf-8") as report_file:
        json.dump(comparison_df.to_dict(orient="records"), report_file, indent=4)

    chart_paths = {
        "metrics": os.path.join(chart_dir, "model_metrics.png"),
        "predictions": os.path.join(chart_dir, "actual_vs_predicted.png"),
        "residuals": os.path.join(chart_dir, "residuals.png"),
        "training": os.path.join(chart_dir, "training_curves.png"),
        "features": os.path.join(chart_dir, "feature_importance_gain.png"),
    }
    _save_metric_chart(comparison_df, chart_paths["metrics"])
    _save_prediction_chart(y_true, predictions, chart_paths["predictions"])
    _save_residual_chart(y_true, predictions, chart_paths["residuals"])
    _save_training_chart(training_history or {}, chart_paths["training"])
    _save_feature_chart(models_dict, list(X_test.columns), chart_paths["features"])

    html_path = os.path.join(reports_dir, "model_report.html")
    _write_html_report(comparison_df, chart_paths, len(y_true), html_path)

    md_path = os.path.join(reports_dir, "model_comparison.md")
    with open(md_path, "w", encoding="utf-8") as report_file:
        report_file.write("# ML Model Comparison & Performance Report\n\n")
        report_file.write("**Developer:** Imtiaj Ahmad (Roll: 2207092)\n\n")
        report_file.write(comparison_df.to_markdown(index=False))
        report_file.write(
            "\n\n*Best model ranked by lowest RMSE; higher R² is also better.*"
            "\n\nOpen [the standalone visual report](model_report.html) for prediction, "
            "residual, training-loss, and feature-gain charts."
        )

    return comparison_df
