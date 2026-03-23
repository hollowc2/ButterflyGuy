-- Migration 005: Add daily_bars table for SPX/VIX daily OHLCV data

CREATE TABLE IF NOT EXISTS daily_bars (
    date        DATE           NOT NULL,
    underlying  TEXT           NOT NULL,
    open        NUMERIC(10,4),
    high        NUMERIC(10,4),
    low         NUMERIC(10,4),
    close       NUMERIC(10,4)  NOT NULL,
    volume      BIGINT         DEFAULT 0,
    PRIMARY KEY (date, underlying)
);
