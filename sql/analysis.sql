-- Рейтинг месяцев по посещаемости
SELECT month_date, visits, visitors, ROUND(bounce_rate * 100, 2) AS bounce_pct
FROM monthly_metrics ORDER BY visits DESC;

-- Показатели вовлечённости по месяцам
SELECT month_date, visits, ROUND(pages_per_visit, 2) AS pages_per_visit,
       avg_duration_sec, ROUND(bounce_rate * 100, 2) AS bounce_pct
FROM monthly_metrics ORDER BY month_date;

-- Годовой итог (уникальных посетителей нельзя суммировать по месяцам)
SELECT year, visits, unique_visitors, ROUND(bounce_rate * 100, 2) AS bounce_pct,
       pages_per_visit, avg_duration_sec
FROM annual_summary ORDER BY year;

-- Месяцы с максимальным показателем отказов
SELECT month_date, ROUND(bounce_rate * 100, 2) AS bounce_pct, visits
FROM monthly_metrics ORDER BY bounce_rate DESC LIMIT 3;

-- Посещаемость по кварталам
SELECT year, ((month - 1) / 3 + 1) AS quarter, SUM(visits) AS visits
FROM monthly_metrics GROUP BY year, quarter ORDER BY year, quarter;
