"""Обработка помесячной выгрузки Яндекс Метрики и сохранение в SQLite и CSV."""
import argparse
import csv
import logging
import sqlite3
from pathlib import Path

LOG = logging.getLogger(__name__)
EXPECTED = ("Месяц визита", "Визиты", "Посетители", "Отказы",
            "Глубина просмотра", "Время на сайте")

def time_seconds(value):
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid time HH:MM:SS: {value}")
    h, m, s = map(int, parts)
    if not 0 <= m < 60 or not 0 <= s < 60 or h < 0:
        raise ValueError(f"Invalid time: {value}")
    return h * 3600 + m * 60 + s

def parse_file(path, year):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or any(c not in reader.fieldnames for c in EXPECTED):
            raise ValueError("Unexpected Metrica CSV columns")
        monthly, annual = [], None
        for raw in reader:
            label = raw["Месяц визита"].strip()
            visits = int(raw["Визиты"])
            visitors = int(raw["Посетители"])
            bounces = float(raw["Отказы"])
            depth = float(raw["Глубина просмотра"])
            duration = time_seconds(raw["Время на сайте"])
            if visits < 0 or visitors < 0 or not 0 <= bounces <= 1 or depth < 0:
                raise ValueError(f"Invalid metrics for {label}")
            if label == "Итого и средние":
                if annual is not None:
                    raise ValueError("Duplicate annual summary")
                annual = (visits, visitors, bounces, depth, duration)
                continue
            month = int(label)
            if not 1 <= month <= 12:
                raise ValueError(f"Invalid month {month}")
            monthly.append({
                "month": month, "month_date": f"{year}-{month:02d}-01",
                "year": year, "visits": visits, "visitors": visitors,
                "bounce_rate": bounces, "bounce_rate_pct": round(bounces * 100, 2),
                "pages_per_visit": depth, "avg_duration_sec": duration,
                "visits_per_visitor": round(visits / visitors, 3) if visitors else 0
            })
    if len(monthly) != 12 or len({r["month"] for r in monthly}) != 12:
        raise ValueError("Expected exactly 12 unique months")
    monthly.sort(key=lambda r: r["month"])
    if annual is None:
        raise ValueError("Annual summary missing")
    if sum(r["visits"] for r in monthly) != annual[0]:
        raise ValueError("Annual visits do not match monthly sum")
    return monthly, annual

def process(input_path, db_path, output_path, year=2024):
    monthly, annual = parse_file(input_path, year)
    db_path, output_path = Path(db_path), Path(output_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql_path.read_text(encoding="utf-8-sig"))
        conn.executemany("""INSERT INTO monthly_metrics
            (month_date, year, month, visits, visitors, bounce_rate,
             pages_per_visit, avg_duration_sec)
            VALUES (:month_date, :year, :month, :visits, :visitors,
                    :bounce_rate, :pages_per_visit, :avg_duration_sec)
            ON CONFLICT(month_date) DO UPDATE SET
            visits=excluded.visits, visitors=excluded.visitors,
            bounce_rate=excluded.bounce_rate,
            pages_per_visit=excluded.pages_per_visit,
            avg_duration_sec=excluded.avg_duration_sec""", monthly)
        conn.execute("""INSERT INTO annual_summary
            (year, visits, unique_visitors, bounce_rate, pages_per_visit, avg_duration_sec)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(year) DO UPDATE SET
            visits=excluded.visits, unique_visitors=excluded.unique_visitors,
            bounce_rate=excluded.bounce_rate, pages_per_visit=excluded.pages_per_visit,
            avg_duration_sec=excluded.avg_duration_sec""", (year, *annual))
        conn.commit()
    columns = ["month_date", "year", "month", "visits", "visitors", "bounce_rate",
               "bounce_rate_pct", "pages_per_visit", "avg_duration_sec", "visits_per_visitor"]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(monthly)
    LOG.info("Processed %s rows; annual visits %s, visitors %s", len(monthly), annual[0], annual[1])
    return {"months": len(monthly), "annual_visits": annual[0],
            "annual_unique_visitors": annual[1], "csv": str(output_path)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--db", default="data/processed/analytics.db")
    parser.add_argument("--output", default="data/processed/datalens_monthly.csv")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    print(process(args.input, args.db, args.output, args.year))
