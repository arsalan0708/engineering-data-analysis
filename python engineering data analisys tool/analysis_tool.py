import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze engineering CSV data for peak stress and plot stress vs time."
    )
    parser.add_argument(
        "--input",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--time-col",
        default="time",
        help="Name of the time column in the CSV.",
    )
    parser.add_argument(
        "--stress-col",
        default="stress",
        help="Name(s) of the stress/load column(s) in the CSV (comma-separated).",
    )
    parser.add_argument(
        "--values",
        help=(
            "Comma-separated stress values. For multiple stress columns, "
            "separate series with ';'."
        ),
    )
    parser.add_argument(
        "--time-values",
        help="Comma-separated time values (optional).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for values interactively instead of reading a CSV.",
    )
    parser.add_argument(
        "--output",
        default="charts/stress_vs_time.png",
        help="Path to save the generated plot image.",
    )
    return parser.parse_args()

def parse_stress_cols(raw: str) -> list:
    cols = [col.strip() for col in raw.split(",") if col.strip()]
    if not cols:
        raise ValueError("At least one stress column must be provided.")
    return cols


def parse_numeric_list(raw: str, label: str) -> list:
    if raw is None:
        return []
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        return []
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value in {label}.") from exc


def parse_series_values(raw: str, stress_cols: list) -> list:
    series_parts = [part.strip() for part in raw.split(";") if part.strip()]
    if len(series_parts) != len(stress_cols):
        raise ValueError(
            "Number of value series must match stress columns "
            f"({len(stress_cols)})."
        )
    series = []
    for idx, part in enumerate(series_parts):
        values = parse_numeric_list(part, f"values for {stress_cols[idx]}")
        if not values:
            raise ValueError(f"No values provided for {stress_cols[idx]}.")
        series.append(values)
    return series


def prepare_data(df: pd.DataFrame, time_col: str, stress_cols: list) -> pd.DataFrame:
    required = [time_col, *stress_cols]
    missing = [col for col in required if col not in df.columns]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing required column(s): {missing_list}")

    df = df[[time_col, *stress_cols]].copy()
    for col in stress_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if not pd.api.types.is_numeric_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    df = df.dropna(subset=[time_col])
    df = df.dropna(subset=stress_cols, how="all")
    if df.empty:
        raise ValueError("No valid rows after cleaning input data.")

    return df


def load_data_from_csv(csv_path: Path, time_col: str, stress_cols: list) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return prepare_data(df, time_col, stress_cols)


def build_data_from_values(
    time_col: str,
    stress_cols: list,
    values_raw: Optional[str],
    time_values_raw: Optional[str],
) -> pd.DataFrame:
    if not values_raw:
        raise ValueError("Values must be provided when no input CSV is used.")

    if len(stress_cols) == 1:
        series = [parse_numeric_list(values_raw, "values")]
        if not series[0]:
            raise ValueError("No values provided.")
    else:
        series = parse_series_values(values_raw, stress_cols)

    length = len(series[0])
    if any(len(values) != length for values in series):
        raise ValueError("All stress value series must be the same length.")

    if time_values_raw:
        time_values = parse_numeric_list(time_values_raw, "time values")
        if len(time_values) != length:
            raise ValueError("Time values must match the length of stress values.")
    else:
        time_values = list(range(length))

    data = {time_col: time_values}
    for col, values in zip(stress_cols, series):
        data[col] = values

    df = pd.DataFrame(data)
    return prepare_data(df, time_col, stress_cols)


def prompt_values(time_col: str, stress_cols: list) -> tuple:
    time_values_raw = input(
        "Enter time values (comma-separated) or leave blank for index: "
    ).strip()
    series_raw = []
    for col in stress_cols:
        values_raw = input(
            f"Enter values for {col} (comma-separated numbers): "
        ).strip()
        if not values_raw:
            raise ValueError(f"No values provided for {col}.")
        series_raw.append(values_raw)
    values_raw = ";".join(series_raw)
    return values_raw, time_values_raw


def find_peaks(df: pd.DataFrame, time_col: str, stress_cols: list) -> dict:
    peaks = {}
    for col in stress_cols:
        series = df[col].dropna()
        if series.empty:
            raise ValueError(f"No valid values for stress column: {col}")
        idx = series.idxmax()
        peak_time = df.loc[idx, time_col]
        peak_stress = df.loc[idx, col]
        peaks[col] = (peak_time, peak_stress)
    return peaks


def compute_stats(df: pd.DataFrame, stress_cols: list) -> dict:
    stats = {}
    for col in stress_cols:
        series = df[col].dropna()
        if series.empty:
            stats[col] = None
            continue
        stats[col] = {
            "count": int(series.count()),
            "min": series.min(),
            "max": series.max(),
            "mean": series.mean(),
            "p95": series.quantile(0.95),
        }
    return stats


def plot_stress(
    df: pd.DataFrame,
    time_col: str,
    stress_cols: list,
    output: Path,
    peaks: dict,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 5))
    color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    for idx, col in enumerate(stress_cols):
        color = color_cycle[idx % len(color_cycle)] if color_cycle else None
        plt.plot(df[time_col], df[col], color=color, linewidth=1.5, label=col)
        peak_time, peak_stress = peaks[col]
        plt.scatter([peak_time], [peak_stress], color=color, zorder=3)
    plt.title("Stress vs Time")
    plt.xlabel(time_col)
    plt.ylabel("Stress / Load" if len(stress_cols) > 1 else stress_cols[0])
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    stress_cols = parse_stress_cols(args.stress_col)

    if args.input:
        csv_path = Path(args.input)
        df = load_data_from_csv(csv_path, args.time_col, stress_cols)
    elif args.interactive or args.values:
        values_raw = args.values
        time_values_raw = args.time_values
        if args.interactive:
            values_raw, time_values_raw = prompt_values(
                args.time_col, stress_cols
            )
        df = build_data_from_values(
            args.time_col, stress_cols, values_raw, time_values_raw
        )
    else:
        raise ValueError("Provide --input, --values, or --interactive.")

    peaks = find_peaks(df, args.time_col, stress_cols)
    stats = compute_stats(df, stress_cols)

    plot_stress(df, args.time_col, stress_cols, output_path, peaks)

    print("Peak values:")
    for col, (peak_time, peak_stress) in peaks.items():
        print(f"- {col}: {peak_stress} at {args.time_col} = {peak_time}")
    print("Summary stats:")
    for col, values in stats.items():
        if values is None:
            print(f"- {col}: no valid values")
            continue
        print(
            f"- {col}: min={values['min']}, max={values['max']}, "
            f"mean={values['mean']}, p95={values['p95']}, count={values['count']}"
        )
    print(f"Chart saved to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
