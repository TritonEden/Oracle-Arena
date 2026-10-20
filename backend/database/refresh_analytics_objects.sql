-- Keep dependencies fresh and commit all four snapshots together.
REFRESH MATERIALIZED VIEW public.player_game_stats_slim;
REFRESH MATERIALIZED VIEW public.player_season_averages;
REFRESH MATERIALIZED VIEW public.mv_game_stats;
REFRESH MATERIALIZED VIEW public.mv_team_win_loss_records;
