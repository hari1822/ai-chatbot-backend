-- Saved via Query Git Saver
-- User: test-user-123
-- Timestamp: 2025-11-07T15:26:56.546684
-- Repository: hari1822/ai-chatbot-backend

SELECT 
    warehouse_name,
    SUM(credits_used) as total_credits
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY total_credits DESC;
