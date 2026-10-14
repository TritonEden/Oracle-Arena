-- Run against the application's PostgreSQL database, in one transaction.
-- Creates missing objects only; never drops source data or existing objects.
-- Refresh in dependency order with refresh_analytics_objects.sql after imports.

CREATE MATERIALIZED VIEW IF NOT EXISTS public.player_game_stats_slim AS
WITH normalized AS (
    SELECT game_id::bigint AS game_id, player_id::integer AS player_id,
           team_id::integer AS team_id,
           CASE WHEN jsonb_typeof(player_game_stats::jsonb) = 'string'
                THEN (player_game_stats::jsonb #>> '{}')::jsonb
                ELSE player_game_stats::jsonb END AS stats,
           (to_jsonb(pgs)->>'id')::bigint AS source_id
    FROM public.player_game_stats pgs
), deduplicated AS (
    SELECT DISTINCT ON (game_id, player_id)
           game_id, player_id, team_id, stats
    FROM normalized
    ORDER BY game_id, player_id,
             (stats->>'PTS' IS NOT NULL) DESC,
             source_id DESC NULLS LAST, stats::text DESC, team_id
)
SELECT game_id, player_id, team_id,
       COALESCE((SELECT jsonb_object_agg(key, value)
                 FROM jsonb_each(CASE WHEN jsonb_typeof(stats) = 'object'
                                      THEN stats ELSE '{}'::jsonb END)
                 WHERE key IN ('MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A',
                               'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB',
                               'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS',
                               'PLUS_MINUS')), '{}'::jsonb)::text AS player_game_stats
FROM deduplicated;

CREATE UNIQUE INDEX IF NOT EXISTS player_game_stats_slim_game_player_idx
    ON public.player_game_stats_slim (game_id, player_id);
CREATE INDEX IF NOT EXISTS player_game_stats_slim_player_idx
    ON public.player_game_stats_slim (player_id, game_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.player_season_averages AS
WITH played AS (
    SELECT pgs.player_id, g.season_year, pgs.player_game_stats::jsonb AS stats
    FROM public.player_game_stats_slim pgs
    JOIN public.games g ON g.game_id::bigint = pgs.game_id
    WHERE CASE
        WHEN pgs.player_game_stats::jsonb->>'MIN' ~ '^[0-9]+([.][0-9]+)?:[0-9]+([.][0-9]+)?$'
        THEN split_part(pgs.player_game_stats::jsonb->>'MIN', ':', 1)::numeric
           + split_part(pgs.player_game_stats::jsonb->>'MIN', ':', 2)::numeric / 60
        WHEN pgs.player_game_stats::jsonb->>'MIN' ~ '^[0-9]+([.][0-9]+)?$'
        THEN (pgs.player_game_stats::jsonb->>'MIN')::numeric
        ELSE 0 END > 0
), values_by_game AS (
    SELECT player_id, season_year, key,
           CASE
               WHEN key = 'MIN' AND value ~ '^[0-9]+([.][0-9]+)?:[0-9]+([.][0-9]+)?$'
               THEN split_part(value, ':', 1)::numeric
                  + split_part(value, ':', 2)::numeric / 60
               WHEN value ~ '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$'
               THEN value::numeric
           END AS numeric_value
    FROM played CROSS JOIN LATERAL jsonb_each_text(stats)
)
SELECT player_id, season_year, key, AVG(numeric_value) AS avg_val
FROM values_by_game
WHERE numeric_value IS NOT NULL
GROUP BY player_id, season_year, key;

CREATE UNIQUE INDEX IF NOT EXISTS player_season_averages_player_season_key_idx
    ON public.player_season_averages (player_id, season_year, key);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_game_stats AS
WITH scores AS (
    SELECT game_id, team_id,
           SUM(CASE WHEN player_game_stats::jsonb->>'PTS'
                         ~ '^[0-9]+([.][0-9]+)?$'
                    THEN (player_game_stats::jsonb->>'PTS')::numeric END) AS score
    FROM public.player_game_stats_slim
    GROUP BY game_id, team_id
)
SELECT g.game_id::bigint AS game_id, g.season_year, g.game_date,
       to_jsonb(g)->>'game_time' AS game_time,
       g.home_team_id::integer AS home_team_id,
       ht.team_location AS home_team_location, ht.team_name AS home_team_name,
       ht.team_abbreviation AS home_team_abbreviation,
       COALESCE(hs.score, 0) AS home_score,
       g.away_team_id::integer AS away_team_id,
       at.team_location AS away_team_location, at.team_name AS away_team_name,
       at.team_abbreviation AS away_team_abbreviation,
       COALESCE(aws.score, 0) AS away_score,
       (to_jsonb(g)->>'winner')::numeric AS winner,
       (to_jsonb(g)->>'total_score_prediction')::numeric AS total_score_prediction
FROM public.games g
LEFT JOIN public.teams ht ON ht.team_id::integer = g.home_team_id::integer
                         AND ht.season_year = g.season_year
LEFT JOIN public.teams at ON at.team_id::integer = g.away_team_id::integer
                         AND at.season_year = g.season_year
LEFT JOIN scores hs ON hs.game_id = g.game_id::bigint
                   AND hs.team_id = g.home_team_id::integer
LEFT JOIN scores aws ON aws.game_id = g.game_id::bigint
                    AND aws.team_id = g.away_team_id::integer;

CREATE UNIQUE INDEX IF NOT EXISTS mv_game_stats_game_idx
    ON public.mv_game_stats (game_id);
CREATE INDEX IF NOT EXISTS mv_game_stats_date_idx
    ON public.mv_game_stats (game_date);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_team_win_loss_records AS
WITH completed AS (
    SELECT * FROM public.mv_game_stats
    WHERE home_score > 0 AND away_score > 0 AND home_score <> away_score
      AND (game_time IS NULL OR game_time ILIKE 'Final%')
), results AS (
    SELECT home_team_id AS target_team_id, season_year,
           (home_score > away_score)::integer AS win,
           (home_score < away_score)::integer AS loss FROM completed
    UNION ALL
    SELECT away_team_id, season_year,
           (away_score > home_score)::integer,
           (away_score < home_score)::integer FROM completed
)
SELECT t.team_id::integer AS target_team_id, t.season_year,
       COALESCE(SUM(r.win), 0)::integer AS wins,
       COALESCE(SUM(r.loss), 0)::integer AS losses,
       COALESCE(SUM(r.win), 0)::text || ' - ' ||
       COALESCE(SUM(r.loss), 0)::text AS wl_record
FROM public.teams t
LEFT JOIN results r ON r.target_team_id = t.team_id::integer
                   AND r.season_year = t.season_year
GROUP BY t.team_id::integer, t.season_year;

CREATE UNIQUE INDEX IF NOT EXISTS mv_team_win_loss_records_team_season_idx
    ON public.mv_team_win_loss_records (target_team_id, season_year);
