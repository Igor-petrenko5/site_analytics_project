# Автоматизированная система анализа посещаемости сайта

Учебный проект: **Python + SQLite/SQL + Apache Airflow 3 + Yandex DataLens**.

## Данные
Использована выгрузка Яндекс Метрики за **январь–декабрь 2024 года**: 12 месяцев и итоговая строка. Исходные данные: `data/raw/metrika_2024_monthly.csv`. Результат: `data/processed/datalens_monthly.csv`.

**Результаты:** 144 432 визита, 119 352 уникальных посетителя за год (из итоговой строки Метрики), показатель отказов 43,87%. Наибольшее количество визитов в январе — 20 386, наименьшее в июне — 7 505.

Важно: суммировать `visitors` за 12 месяцев для определения уникальных посетителей года нельзя.

## Этап 2 — Python и SQL

Скрипт проверяет столбцы и корректность исходных данных, переводит длительность в секунды, сохраняет месячные метрики и годовой итог в SQLite, экспортирует CSV для DataLens.

```powershell
python src/process_metrics.py --input data/raw/metrika_2024_monthly.csv --db data/processed/analytics.db --output data/processed/datalens_monthly.csv
```

Таблицы создаются из `sql/schema.sql`, аналитические запросы — в `sql/analysis.sql`. База `analytics.db` генерируется локально, поэтому в репозиторий не включена.

## Этап 3 — Apache Airflow

DAG: `dags/site_analytics_dag.py`. Три задачи:

```
validate_source → transform_and_save → success_log
```

Расписание: 1-е число каждого месяца, 06:00 (Москва). `catchup=False`.

При работе с официальным Docker Compose Airflow 3 разместите папку проекта по пути `./dags/site_analytics_project` рядом с файлом `./dags/site_analytics_dag.py`. Путь внутри контейнера по умолчанию: `/opt/airflow/dags/site_analytics_project`. При необходимости укажите `SITE_ANALYTICS_ROOT`. У Airflow worker должны быть права на запись в `data/processed`.

**Важно:** DAG повторно обрабатывает статичный CSV за 2024 год, а не скачивает свежие данные Метрики автоматически.

## Этап 4 — DataLens

Загрузите `data/processed/datalens_monthly.csv` как файловое подключение в [Yandex DataLens](https://datalens.yandex.ru/), создайте датасет и графики:

- Визиты по месяцам: `month_date`, `SUM(visits)`.
- Посетители по месяцам: `month_date`, `SUM(visitors)` (только помесячная динамика).
- Отказы: `month_date`, `AVG(bounce_rate_pct)`.
- Время визита: `month_date`, `AVG(avg_duration_sec)`.
- Глубина просмотра: `month_date`, `AVG(pages_per_visit)`.

**Ссылка на опубликованный DataLens-дашборд:** добавьте после публикации. Альтернатива — разместите скриншот в `screenshots/datalens_dashboard.png`.

**Подтверждение Airflow:** разместите скриншот выполненного DAG в `screenshots/airflow_success.png`.

## Ограничения исследования

Предоставлен **помесячный**, а не подневный отчёт. В нём отсутствуют время суток, URL страниц и достижения целей. По текущему источнику нельзя достоверно вычислить самые посещаемые часы, наиболее популярные страницы или конверсии. Для полного выполнения первоначального задания нужны дополнительные отчёты Метрики.

## Материалы для проверки

- `src/process_metrics.py` — код обработки.
- `sql/schema.sql`, `sql/analysis.sql` — схема и аналитика SQL.
- `dags/site_analytics_dag.py` — DAG Airflow.
- `data/processed/datalens_monthly.csv` — источник DataLens.
- Скриншоты / ссылка DataLens — добавить отдельно.
