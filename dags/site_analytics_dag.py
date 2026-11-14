"""Airflow 3.x: проверка CSV -> обработка SQLite -> логирование результата."""
import logging
import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

DATA_ROOT = Path(os.environ.get(
    "SITE_ANALYTICS_ROOT", "/opt/airflow/dags/site_analytics_project"
))

@dag(
    dag_id="site_analytics_monthly_2024",
    description="Validate, transform and export Metrica monthly traffic metrics",
    schedule="0 6 1 * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Moscow"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["metrika", "analytics", "datalens"],
)
def site_analytics():
    @task
    def validate_source():
        from importlib.machinery import SourceFileLoader
        source_file = DATA_ROOT / "data/raw/metrika_2024_monthly.csv"
        script = DATA_ROOT / "src/process_metrics.py"
        if not source_file.is_file() or not script.is_file():
            raise FileNotFoundError(f"Check input file and processor in {DATA_ROOT}")
        module = SourceFileLoader("metrics_processor", str(script)).load_module()
        monthly, annual = module.parse_file(source_file, 2024)
        logging.info("Validated %s months, yearly visits: %s", len(monthly), annual[0])
        return len(monthly)

    @task
    def transform_and_save(_validated_rows):
        from importlib.machinery import SourceFileLoader
        script = DATA_ROOT / "src/process_metrics.py"
        module = SourceFileLoader("metrics_processor", str(script)).load_module()
        return module.process(
            DATA_ROOT / "data/raw/metrika_2024_monthly.csv",
            DATA_ROOT / "data/processed/analytics.db",
            DATA_ROOT / "data/processed/datalens_monthly.csv",
            2024,
        )

    @task
    def success_log(result):
        logging.info(
            "Success: %s months, %s visits; DataLens file: %s",
            result["months"], result["annual_visits"], result["csv"]
        )

    success_log(transform_and_save(validate_source()))

site_analytics()
