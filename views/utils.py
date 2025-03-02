from database import SessionDep
from sqlalchemy import text


# Метрики ######################################
async def herfindahl_hirschman_rate(supplier_id: int, db: SessionDep):
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
        s.id = {supplier_id}  -- Здесь подставляется ID интересующего поставщика
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
    SUM(POWER(market_share, 2)) AS hhi_index
FROM 
    market_shares
GROUP BY 
    supplier_id, supplier_name;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


async def suppliers_success_rate(db: SessionDep):
    """
    Функция для расчета успешности поставщика
    """

    result = await db.execute(
        text(
            """
SELECT 
    s.id AS supplier_id,
    s.name AS supplier_name,
    s.inn,
    r.name AS region_name,
    COUNT(DISTINCT p.id_ks) AS sessions_participated,
    COUNT(DISTINCT ks.id_ks) AS sessions_won,
    COUNT(DISTINCT ks.id_ks) * 100.0 / COUNT(DISTINCT p.id_ks) AS win_rate_percent,
    AVG((ks.start_price - ks.end_price) / ks.start_price * 100) AS avg_price_reduction_percent
FROM 
    suppliers s
JOIN 
    regions r ON r.id = s.region_id
LEFT JOIN 
    participants p ON p.id_participant = s.id
LEFT JOIN 
    ks ON ks.winner_id = s.id
GROUP BY 
    s.id, s.name, s.inn, r.name
HAVING 
    COUNT(DISTINCT p.id_ks) > 0 -- Только поставщики, которые участвовали хотя бы в одной сессии
ORDER BY 
    sessions_won DESC, win_rate_percent DESC LIMIT 20;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


async def price_reduction_by_kpgz_categories_rate(db: SessionDep):
    """
    Функция для анализа снижения цен по категориям КПГЗ
    """

    result = await db.execute(
        text(
            """
SELECT 
    k.id,
    k.code,
    k.name AS kpgz_name,
    COUNT(ks.id_ks) AS total_sessions,
    AVG(ks.start_price) AS avg_start_price,
    AVG(ks.end_price) AS avg_end_price,
    AVG(ks.start_price - ks.end_price) AS avg_price_reduction,
    100 - AVG((ks.start_price - ks.end_price) / ks.start_price * 100) AS avg_price_reduction_percent
FROM 
    kpgz_categories k
JOIN 
    cte c ON c.kpgz_id = k.id
JOIN 
    orders o ON o.id_cte = c.id
JOIN 
    ks ON ks.id_ks = o.id_ks
GROUP BY 
    k.id, k.code, k.name
ORDER BY 
    avg_price_reduction_percent DESC;
            """
        )
    )
    return result.scalars()._fetchiter_impl()


async def share_wins_rate(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    """
    Функция для расчета доли побед поставщика
    """

    result = await db.execute(
        text(
            f"""
SELECT ROUND(
         (COUNT(ks.id_ks) * 100.0 / 
          (SELECT COUNT(*) 
           FROM ks 
           WHERE ks.end_ks BETWEEN {start_date} AND {end_date})
         ), 2) AS win_rate
FROM ks
JOIN suppliers ON suppliers.id = ks.winner_id
WHERE suppliers.id = {supplier_id}
  AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
"""
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_rate(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    """
    Функция для расчета выручки поставщика
    """

    result = await db.execute(
        text(
            f"""
SELECT SUM(ks.end_price) AS my_revenue
FROM ks
JOIN suppliers ON suppliers.id = ks.winner_id
WHERE suppliers.id = {supplier_id}
  AND ks.end_ks BETWEEN '{start_date}' AND '{end_date}'
        """
        )
    )

    return result.scalars()._fetchiter_impl()


async def average_price_reduction(
    supplier_id: int, start_date: str, end_date: str, db: SessionDep
):
    """
    Функция для расчета среднего снижения цены поставщика
    """

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

    return result.scalars()._fetchiter_impl()


# Графики ######################################


async def revenue_by_customers_with_selected_consolidated_kpgz(
    supplier_id: int,
    consolidated_kpgz: int,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    """
    Функция для расчета выручки поставщика по выбранным заказчикам и КПГЗ
    """

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
    AND kc.id = {consolidated_kpgz}  -- Укрупненный КПГЗ
GROUP BY cus.name
ORDER BY total_revenue DESC;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_by_customers_with_selected_region(
    winner_id: int,
    region_id: int,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    """
    Функция для расчета выручки поставщика по выбранным заказчикам и КПГЗ
    """

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
WHERE s.id = {winner_id}  -- ID поставщика
    AND ks.end_ks BETWEEN {start_date} AND {end_date}  -- Период
    AND r.id = {region_id}  -- Регион
GROUP BY cus.name
ORDER BY total_revenue DESC
LIMIT 10;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_for_specific_period(
    supplier_id: int, period: str, start_date: str, end_date: str, db: SessionDep
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('{period}', '{start_date}'::date),
    date_trunc('{period}', '{end_date}'::date),
    interval '1 {period}'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('{period}', ks.start_ks) AS {period},
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.start_ks BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY date_trunc('{period}', ks.start_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS {period},
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.{period} = m.month_start
ORDER BY m.month_start;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_for_specific_period_by_kpgz(
    supplier_id: int,
    kpgz_category_id: str,
    period: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('{period}', '{start_date}'::date),
    date_trunc('{period}', '{end_date}'::date),
    interval '1 {period}'
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
    date_trunc('{period}', ks.end_ks) AS {period},
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN relevant_orders ro ON ks.id_ks = ro.id_ks
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN {start_date} AND {end_date}
  GROUP BY date_trunc('{period}', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS {period},
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.{period} = m.month_start
ORDER BY m.month_start;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_for_specific_period_by_region(
    supplier_id: int,
    region_id: str,
    period: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('{period}', '{start_date}'::date),
    date_trunc('{period}', '{end_date}'::date),
    interval '1 {period}'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('{period}', ks.start_ks) AS {period},
    SUM(CAST(ks.end_price AS numeric)) AS total_revenue
  FROM ks
  JOIN customers c ON ks.customer_id = c.id
  WHERE ks.winner_id = {supplier_id}
    AND ks.end_ks BETWEEN {start_date} AND {end_date}
    AND c.region_id = {region_id}
  GROUP BY date_trunc('{period}', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS {period},
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.{period} = m.month_start
ORDER BY m.month_start;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_for_specific_period_by_kpgz_and_region(
    supplier_id: int,
    region_id: str,
    kpgz_category_id: str,
    period: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
WITH months AS (
  SELECT generate_series(
    date_trunc('{period}', '{start_date}'::date),
    date_trunc('{period}', '{end_date}'::date),
    interval '1 {period}'
  ) AS month_start
),
agg AS (
  SELECT
    date_trunc('{period}', ks.end_ks) AS {period},
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
  GROUP BY date_trunc('{period}', ks.end_ks)
)
SELECT
  to_char(m.month_start, 'YYYY-MM') AS {period},
  COALESCE(a.total_revenue, 0) AS total_revenue
FROM months m
LEFT JOIN agg a ON a.{period} = m.month_start
ORDER BY m.month_start;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_kpgz(
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    kc.name AS aggregated_kpgz,
    SUM(o.count * o.oferta_price)/1000000 AS total_revenue
FROM orders o
JOIN ks k ON o.id_ks = k.id_ks
JOIN cte c ON o.id_cte = c.id
JOIN kpgz_details kd ON c.kpgz_id = kd.id
JOIN kpgz_categories kc ON kd.parent_id = kc.id
WHERE k.start_ks BETWEEN '{start_date}' AND '{end_date}'
GROUP BY kc.name
ORDER BY total_revenue DESC
LIMIT 10;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_kpgz_by_region(
    region_id: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
        kc.code || ' ' || kc.name AS category_name,
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
        kc.code, kc.name
  ORDER BY revenue DESC
  LIMIT 10
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_kpgz_by_kpgz(
    kpgz_category_id: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
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
LIMIT 10;
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_kpgz_by_kpgz_and_region(
    region_id: str,
    kpgz_category_id: str,
    start_date: str,
    end_date: str,
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
    AND kc.id = {kpgz_category_id}'
GROUP BY 
    kd.code, kd.name
ORDER BY 
    revenue DESC
LIMIT 10
            """
        )
    )

    return result.scalars()._fetchiter_impl()


async def revenue_by_region(
    supplier_id: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
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


async def revenue_by_region_1(
    winner_id: str,
    region_id: str,
    start_date: str,
    end_date: str,
    db: SessionDep,
):
    result = await db.execute(
        text(
            f"""
SELECT 
    kc.code || ' ' || kc.name AS kpgz_category,
    SUM(o.oferta_price * o.count) AS total_revenue
FROM orders as o
JOIN ks as k ON o.id_ks = k.id_ks
JOIN customers as cust ON k.customer_id = cust.id
JOIN cte ON o.id_cte = cte.id
JOIN kpgz_details as kd ON cte.kpgz_id = kd.id
JOIN kpgz_categories as kc ON kd.parent_id = kc.id
WHERE k.winner_id = {winner_id}
  AND k.end_ks BETWEEN {start_date} AND {end_date}
  AND cust.region_id = {region_id}
GROUP BY kc.name, kc.code
ORDER BY total_revenue DESC
LIMIT 10;
            """
        )
    )

    return result.scalars()._fetchiter_impl()
