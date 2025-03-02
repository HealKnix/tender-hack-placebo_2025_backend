from database import SessionDep
from sqlalchemy import text


async def herfindahl_hirschman_rate(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    """
    Функция для расчета индекса Херфиндаля-Хиршмана
    """

    result = await db.execute(
        text(
            f"""
WITH supplier_customers AS (
    -- Выбираем всех заказчиков для конкретного поставщика
    SELECT 
        s.id AS supplier_id,
        s.name AS supplier_name,
        c.id AS customer_id,
        c.name AS customer_name,
        COUNT(ks.id_ks) AS num_orders,
        SUM(ks.end_price) AS total_value
    FROM 
        suppliers s
    JOIN 
        ks ON s.id = ks.winner_id
    JOIN 
        customers c ON ks.customer_id = c.id
    WHERE 
        s.id = {supplier_id} 
    AND ks.end_ks BETWEEN '{start_date}'  AND '{end_date}'  -- Здесь подставляется ID интересующего поставщика
    GROUP BY 
        s.id, s.name, c.id, c.name
),
totals AS (
    -- Рассчитываем общую сумму заказов для поставщика
    SELECT 
        supplier_id,
        supplier_name,
        SUM(total_value) AS grand_total
    FROM 
        supplier_customers
    GROUP BY 
        supplier_id, supplier_name
),
market_shares AS (
    -- Рассчитываем долю каждого заказчика
    SELECT 
        sc.supplier_id,
        sc.supplier_name,
        sc.customer_id,
        sc.customer_name,
        sc.total_value,
        t.grand_total,
        (sc.total_value / t.grand_total * 100) AS market_share
    FROM 
        supplier_customers sc
    JOIN 
        totals t ON sc.supplier_id = t.supplier_id
)
-- Рассчитываем индекс Херфиндаля-Хиршмана
SELECT 
    ROUND(SUM(POWER(market_share, 2)),2) AS hhi_index
FROM 
    market_shares
GROUP BY 
    supplier_id, supplier_name;
            """
        )
    )
    return {"hhi_index": result.scalar()}


async def metric_percentage_wins(
    supplier_id: int,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT ROUND(
         (COUNT(ks.id_ks) * 100.0 / 
          (SELECT COUNT(*) 
           FROM ks 
           WHERE ks.end_ks BETWEEN '{start_date}' AND '{end_date}')
         ), 2) AS win_rate
FROM ks
JOIN suppliers ON suppliers.id = ks.winner_id
WHERE suppliers.id = {supplier_id}
  AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
            """
        )
    )
    return {"win_rate": result.scalar()}


async def metric_avg_downgrade_cost(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
    ROUND(AVG(
        (CAST(k.start_price AS numeric) - CAST(k.end_price AS numeric)) 
        / CAST(k.start_price AS numeric) * 100
    ),2) AS avg_reduction_percent
FROM ks k
JOIN suppliers s ON k.winner_id = s.id
WHERE s.id = {supplier_id}
  AND k.start_ks BETWEEN '{start_date}' AND '{end_date}'
GROUP BY s.id;
            """
        )
    )
    return {"avg_reduction_percent": result.scalar()}


async def metric_total_revenue(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT SUM(ks.end_price) AS my_revenue
FROM ks
WHERE ks.winner_id = {supplier_id}
  AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
            """
        )
    )
    return {"my_revenue": result.scalar()}


# График 2 состояние 1
async def revenue_by_regions(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
    r.name AS region_name,
    SUM(o.count * o.oferta_price) AS revenue
FROM ks
JOIN orders o ON ks.id_ks = o.id_ks
JOIN customers c ON ks.customer_id = c.id
JOIN regions r ON c.region_id = r.id
WHERE 
    ks.winner_id = {supplier_id} 
    AND ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
GROUP BY r.name
ORDER BY revenue DESC
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 2 состояние 2
async def revenue_by_kpgz_category_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    kc.code AS kpgz_category,
    SUM(o.oferta_price * o.count) AS total_revenue
FROM orders as o
JOIN ks as k ON o.id_ks = k.id_ks
JOIN customers as cust ON k.customer_id = cust.id
JOIN cte ON o.id_cte = cte.id
JOIN kpgz_details as kd ON cte.kpgz_id = kd.id
JOIN kpgz_categories as kc ON kd.parent_id = kc.id
WHERE k.winner_id = {supplier_id}
  AND k.end_ks BETWEEN '{start_date}' AND '{end_date}'
  AND cust.region_id = {region_id}
GROUP BY kc.code
ORDER BY total_revenue DESC
LIMIT {limit};
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 2 состояние 3
async def revenue_by_kpgz_category_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    reg.name,
    SUM(o.oferta_price * o.count) AS total_revenue
FROM orders as o
JOIN ks as k ON o.id_ks = k.id_ks
JOIN customers as cust ON k.customer_id = cust.id
JOIN cte ON o.id_cte = cte.id
JOIN kpgz_details as kd ON cte.kpgz_id = kd.id
JOIN kpgz_categories as kc ON kd.parent_id = kc.id
JOIN regions as reg ON cust.region_id = reg.id
WHERE k.winner_id = {supplier_id}
  AND k.end_ks BETWEEN '{start_date}' AND '{end_date}'
  AND kc.id = {kpgz_category_id}
GROUP BY reg.name
ORDER BY total_revenue DESC
LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 2 состояние 4
async def revenue_by_kpgz_category_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
        kd.code || ' ' || kd.name AS kpgz_detail_name,
        SUM(CAST(o.oferta_price AS numeric) * o.count) AS revenue
    FROM 
        ks
    JOIN 
        orders o ON ks.id_ks = o.id_ks
    JOIN 
        cte ON o.id_cte = cte.id
    JOIN 
        kpgz_details kd ON cte.kpgz_id = kd.id
    JOIN 
        kpgz_categories kc ON kd.parent_id = kc.id
    JOIN 
        suppliers s ON ks.winner_id = s.id
    JOIN
        customers c ON ks.customer_id = c.id
    WHERE 
        s.id = {supplier_id}                         -- Параметр: ID поставщика
        AND c.region_id = {region_id}                -- Параметр: ID региона заказчика
        AND ks.start_ks >= '{start_date}'              -- Параметр: начало периода
        AND ks.end_ks <= '{end_date}'                  -- Параметр: конец периода
        AND kc.id = {kpgz_category_id}               -- Параметр: ID укрупненной категории КПГЗ
    GROUP BY 
        kd.code, kd.name
    ORDER BY 
        revenue DESC
  LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 1 состояние 1
async def total_revenue_by_kpgz_category(
    start_date: str, end_date: str, limit: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
    kc.code AS aggregated_kpgz,
    SUM(o.count * o.oferta_price)/1000000 AS total_revenue
FROM orders o
JOIN ks k ON o.id_ks = k.id_ks
JOIN cte c ON o.id_cte = c.id
JOIN kpgz_details kd ON c.kpgz_id = kd.id
JOIN kpgz_categories kc ON kd.parent_id = kc.id
WHERE k.start_ks BETWEEN '{start_date}' AND '{end_date}'
GROUP BY kc.code
ORDER BY total_revenue DESC
LIMIT {limit}

            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 1 состояние 2 выбран регион
async def total_revenue_by_kpgz_category_by_region_id(
    start_date: str, end_date: str, region_id: int, limit: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
        kc.code AS category_name,
        SUM(o.count * o.oferta_price) / 1000000 AS revenue
    FROM 
        orders o
    JOIN 
        ks ON o.id_ks = ks.id_ks
    JOIN 
        customers c ON ks.customer_id = c.id
    JOIN 
        regions r ON c.region_id = r.id
    JOIN 
        cte ON o.id_cte = cte.id
    JOIN 
        kpgz_details kd ON cte.kpgz_id = kd.id
    JOIN 
        kpgz_categories kc ON kd.parent_id = kc.id
    WHERE 
        ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
        AND c.region_id = {region_id}
    GROUP BY 
        kc.code
  ORDER BY revenue DESC
  LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 1 состояние 3 выбран КПГЗ
async def total_revenue_by_regions_by_kpgz_category_id(
    start_date: str, end_date: str, kpgz_category_id: int, limit: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
    r.name AS region,
    SUM(o.count * o.oferta_price)/1000000 AS total_revenue
FROM orders o
JOIN ks k ON o.id_ks = k.id_ks
JOIN suppliers s ON k.winner_id = s.id
JOIN regions r ON s.region_id = r.id
JOIN cte c ON o.id_cte = c.id
JOIN kpgz_details kd ON c.kpgz_id = kd.id
JOIN kpgz_categories kc ON kd.parent_id = kc.id
WHERE k.start_ks BETWEEN '{start_date}' AND '{end_date}'
  AND kc.id = {kpgz_category_id}
GROUP BY r.name
ORDER BY total_revenue DESC
LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 1 состояние 4 выбран КПГЗ и регион
async def total_revenue_by_regions_by_kpgz_category_and_region_id(
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    kd.code || ' ' || kd.name AS detailed_kpgz_name,
    SUM(o.count * o.oferta_price) / 1000000 AS revenue
FROM 
    orders o
JOIN 
    ks ON o.id_ks = ks.id_ks
JOIN 
    cte ON o.id_cte = cte.id
JOIN 
    kpgz_details kd ON cte.kpgz_id = kd.id
JOIN 
    kpgz_categories kc ON kd.parent_id = kc.id
JOIN 
    customers c ON ks.customer_id = c.id
JOIN 
    regions r ON c.region_id = r.id
WHERE 
    ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
    AND r.id = {region_id}
    AND kc.id = {kpgz_category_id}
GROUP BY 
    kd.code, kd.name
ORDER BY 
    revenue DESC
LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 1 по месяцам
async def revenue_trend_by_mounth(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('month', '{start_date}'::date),
    date_trunc('month', '{end_date}'::date),
    interval '1 month'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('month', ks.start_ks) AS month,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY date_trunc('month', ks.start_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS month,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.month = m.month_start
ORDER BY m.month_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 1 по неделям
async def revenue_trend_by_weeks(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
WITH weeks AS (
  SELECT generate_series(
    date_trunc('week', '{start_date}'::date),
    date_trunc('week', '{end_date}'::date),
    interval '1 week'
  ) AS week_start
),
agg AS (
  SELECT
    date_trunc('week', ks.start_ks) AS week,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY date_trunc('week', ks.start_ks)
)
SELECT
  to_char(w.week_start, 'YYYY-"W"IW') AS week,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM weeks w
LEFT JOIN agg a ON a.week = w.week_start
ORDER BY w.week_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 2 по месяцам
async def revenue_trend_by_mounth_by_region_id(
    supplier_id: int, start_date: str, end_date: str, region_id: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('month', '{start_date}'::date),
    date_trunc('month', '{end_date}'::date),
    interval '1 month'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('month', ks.start_ks) AS month,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN customers c ON ks.customer_id = c.id
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
    AND c.region_id = {region_id}
  GROUP BY date_trunc('month', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS month,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.month = m.month_start
ORDER BY m.month_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 2 по неделям
async def revenue_trend_by_weeks_by_region_id(
    supplier_id: int, start_date: str, end_date: str, region_id: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
WITH weeks AS (
  SELECT generate_series(
    date_trunc('week', '{start_date}'::date),
    date_trunc('week', '{end_date}'::date),
    interval '1 week'
  ) AS week_start
),
agg AS (
  SELECT
    date_trunc('week', ks.start_ks) AS week,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN customers c ON ks.customer_id = c.id
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
    AND c.region_id = {region_id}
  GROUP BY date_trunc('week', ks.end_ks)
)
SELECT
  to_char(w.week_start, 'YYYY-"W"IW') AS week,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM weeks w
LEFT JOIN agg a ON a.week = w.week_start
ORDER BY w.week_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 3 по месяцам
async def revenue_trend_by_mounth_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('month', '{start_date}'::date),
    date_trunc('month', '{end_date}'::date),
    interval '1 month'
  ) AS month_start
),
filtered_kpgz AS (
  SELECT kd.id
  FROM kpgz_details kd
  WHERE kd.parent_id = {kpgz_category_id}
),
relevant_orders AS (
  SELECT o.id_ks
  FROM orders o
  JOIN cte c ON o.id_cte = c.id
  JOIN filtered_kpgz fk ON c.kpgz_id = fk.id
),
agg AS (
  SELECT
    date_trunc('month', ks.end_ks) AS month,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN relevant_orders ro ON ks.id_ks = ro.id_ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY date_trunc('month', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS month,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.month = m.month_start
ORDER BY m.month_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 3 по неделям
async def revenue_trend_by_weeks_by_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH weeks AS (
  SELECT generate_series(
    date_trunc('week', '{start_date}'::date),
    date_trunc('week', '{end_date}'::date),
    interval '1 week'
  ) AS week_start
),
filtered_kpgz AS (
  SELECT kd.id
  FROM kpgz_details kd
  WHERE kd.parent_id = {kpgz_category_id}
),
relevant_orders AS (
  SELECT o.id_ks
  FROM orders o
  JOIN cte c ON o.id_cte = c.id
  JOIN filtered_kpgz fk ON c.kpgz_id = fk.id
),
agg AS (
  SELECT
    date_trunc('week', ks.end_ks) AS week,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN relevant_orders ro ON ks.id_ks = ro.id_ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY date_trunc('week', ks.end_ks)
)
SELECT
  to_char(w.week_start, 'YYYY-"W"IW') AS week,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM weeks w
LEFT JOIN agg a ON a.week = w.week_start
ORDER BY w.week_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 4 по месяцам
async def revenue_trend_by_mounth_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('month', '{start_date}'::date),
    date_trunc('month', '{end_date}'::date),
    interval '1 month'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('month', ks.end_ks) AS month,
    SUM(o.oferta_price * o.count) AS total_revenue
  FROM ks
  JOIN customers c ON ks.customer_id = c.id
  JOIN orders o ON ks.id_ks = o.id_ks
  JOIN cte ON o.id_cte = cte.id
  JOIN kpgz_details kd ON cte.kpgz_id = kd.id
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
    AND c.region_id = {region_id}
    AND kd.parent_id = {kpgz_category_id}
  GROUP BY date_trunc('month', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS month,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.month = m.month_start
ORDER BY m.month_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 3 состояние 4 по месяцам
async def revenue_trend_by_weeks_by_kpgz_category_id_and_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH weeks AS (
  SELECT generate_series(
    date_trunc('week', '{start_date}'::date),
    date_trunc('week', '{end_date}'::date),
    interval '1 week'
  ) AS week_start
),
agg AS (
  SELECT
    date_trunc('week', ks.end_ks) AS week,
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN customers c ON ks.customer_id = c.id
  JOIN orders o ON ks.id_ks = o.id_ks
  JOIN cte ON o.id_cte = cte.id
  JOIN kpgz_details kd ON cte.kpgz_id = kd.id
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
    AND c.region_id = {region_id}
    AND kd.parent_id = {kpgz_category_id}
  GROUP BY date_trunc('week', ks.end_ks)
)
SELECT
  to_char(w.week_start, 'YYYY-"W"IW') AS week,
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM weeks w
LEFT JOIN agg a ON a.week = w.week_start
ORDER BY w.week_start;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 4 состояние 1 по месяцам
async def revenue_by_customers(
    supplier_id: int, start_date: str, end_date: str, limit: int, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
SELECT 
    c.name AS customer_name,
    SUM(o.oferta_price * o.count) AS total_revenue
FROM orders as o
JOIN ks as k ON o.id_ks = k.id_ks
JOIN customers as c ON k.customer_id = c.id
WHERE k.winner_id = {supplier_id}
AND k.end_ks BETWEEN '{start_date}' AND '{end_date}'
GROUP BY c.name
ORDER BY total_revenue DESC
LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 4 состояние 2 по месяцам когда выбран регион
async def revenue_by_customers_by_region_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    region_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    cus.name AS customer_name,
    SUM(o.count * o.oferta_price) AS total_revenue
FROM orders o
JOIN ks ON o.id_ks = ks.id_ks
JOIN customers AS cus ON ks.customer_id = cus.id
JOIN suppliers AS s ON ks.winner_id = s.id
JOIN regions AS r ON cus.region_id = r.id
WHERE s.id = {supplier_id}  -- ID поставщика
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'  -- Период
    AND r.id = {region_id}  -- Регион
GROUP BY cus.name
ORDER BY total_revenue DESC
LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 4 состояние 3 по месяцам когда выбран КПГЗ
async def revenue_by_customers_by_kpgz_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    cus.name AS customer_name,
    SUM(o.count * o.oferta_price) AS total_revenue
FROM orders AS o
JOIN ks ON o.id_ks = ks.id_ks
JOIN customers AS cus ON ks.customer_id = cus.id
JOIN suppliers AS s ON ks.winner_id = s.id
JOIN cte ON o.id_cte = cte.id
JOIN kpgz_details AS kd ON cte.kpgz_id = kd.id
JOIN kpgz_categories AS kc ON kd.parent_id = kc.id
WHERE s.id = {supplier_id}  -- ID поставщика
    AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'  -- Период
    AND kc.id = {kpgz_category_id}  -- Укрупненный КПГЗ
GROUP BY cus.name
ORDER BY total_revenue DESC;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


# График 4 состояние 4 когда выбран КПГЗ и регион
async def revenue_by_customers_by_region_id_and_kpgz_category_id(
    supplier_id: int,
    start_date: str,
    end_date: str,
    kpgz_category_id: int,
    region_id,
    limit: int,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
        c.name AS customer_name,
        SUM(o.oferta_price * o.count) AS revenue
    FROM
        ks
    JOIN customers c ON ks.customer_id = c.id
    JOIN regions r ON c.region_id = r.id
    JOIN orders o ON ks.id_ks = o.id_ks
    JOIN cte ON o.id_cte = cte.id
    JOIN kpgz_details kd ON cte.kpgz_id = kd.id
    JOIN kpgz_categories kc ON kd.parent_id = kc.id
    WHERE
        ks.winner_id = {supplier_id}
        AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
        AND kc.id = {kpgz_category_id}
        AND r.id = {region_id}
    GROUP BY
        c.name
    ORDER BY revenue DESC
    LIMIT {limit}
            """
        )
    )
    return result.scalars()._fetchiter_impl()
