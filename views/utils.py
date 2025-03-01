from database import SessionDep
from sqlalchemy import text


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
    supplier s
JOIN 
    ks ON s.id = ks.winner_id
JOIN 
    customer c ON ks.customer_id = c.id
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
supplier_id,
supplier_name,
SUM(POWER(market_share, 2)) AS hhi_index,
COUNT(customer_id) AS total_customers
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
    supplier s
JOIN 
    region r ON r.id = s.region_id
LEFT JOIN 
    participant p ON p.id_participant = s.id
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
    k.code_kpgz,
    k.name AS kpgz_name,
    COUNT(ks.id_ks) AS total_sessions,
    AVG(ks.start_price) AS avg_start_price,
    AVG(ks.end_price) AS avg_end_price,
    AVG(ks.start_price - ks.end_price) AS avg_price_reduction,
    100 - AVG((ks.start_price - ks.end_price) / ks.start_price * 100) AS avg_price_reduction_percent
FROM 
    kpgz k
JOIN 
    cte c ON c.kpgz_id = k.id
JOIN 
    "order" o ON o.id_cte = c.id
JOIN 
    ks ON ks.id_ks = o.id_ks
GROUP BY 
    k.id, k.code_kpgz, k.name
ORDER BY 
    avg_price_reduction_percent DESC;
            """
        )
    )
    return result.scalars()._fetchiter_impl()
