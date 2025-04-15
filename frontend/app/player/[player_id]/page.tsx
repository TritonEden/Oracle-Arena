"use client";

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import styles from "./playerDetail.module.css";

interface PlayerGameStats {
  game_id: string;
  stats: { [key: string]: any };
}

const PlayerDetail: React.FC = () => {
  const { player_id } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const season_year = searchParams.get("season") ?? "2024-25";
  const team_id = searchParams.get("team_id");

  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingName, setLoadingName] = useState(true);
  const [playerName, setPlayerName] = useState<string>("");

  // Fetch player name
  useEffect(() => {
    fetch(`http://localhost:8000/api/players/`)
      .then((res) => res.json())
      .then((data) => {
        const foundPlayer = data.find((p: any) => p.player_id.toString() === player_id);
        if (foundPlayer) {
          setPlayerName(`${foundPlayer.first_name} ${foundPlayer.last_name}`);
        }
        setLoadingName(false);
      })
      .catch((err) => {
        console.error("Failed to fetch player name", err);
        setLoadingName(false);
      });
  }, [player_id]);

  // Fetch stats
  useEffect(() => {
    fetch(`http://localhost:8000/api/player_stats_for_season/${player_id}/${season_year}/`)
      .then((res) => res.json())
      .then((data) => {
        const parsed: PlayerGameStats[] = data.map((entry: any) => ({
          game_id: entry.game_id,
          stats: JSON.parse(entry.player_game_stats),
        }));

        setStats(parsed.sort((a, b) => b.game_id.localeCompare(a.game_id)));
        setLoadingStats(false);
      })
      .catch((err) => {
        console.error("Error fetching player season stats:", err);
        setLoadingStats(false);
      });
  }, [player_id, season_year]);

  const isLoading = loadingStats || loadingName;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.back}>
          <button
            className={styles.backButton}
            onClick={() =>
              router.push(team_id ? `/team_players/${team_id}/${season_year}` : "/statistics")
            }
          >
            <span>&lt;</span> Back to Players
          </button>
        </div>
        <h2>
          {isLoading ? "Loading..." : `${playerName} - Stats for ${season_year}`}
        </h2>
      </div>

      {isLoading ? (
        <p>Loading...</p>
      ) : stats.length > 0 ? (
        <div className={styles.statsTable}>
          <table className={styles.statsTableContainer}>
            <thead>
              <tr>
                <th>MIN</th><th>FGM</th><th>FGA</th><th>FG%</th><th>FG3M</th><th>FG3A</th><th>FG3%</th>
                <th>FTM</th><th>FTA</th><th>FT%</th><th>OREB</th><th>DREB</th><th>REB</th>
                <th>AST</th><th>STL</th><th>BLK</th><th>TO</th><th>PF</th><th>PTS</th><th>+/-</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((stat, index) => (
                <tr key={index}>
                  <td>{stat.stats.MIN}</td>
                  <td>{stat.stats.FGM}</td>
                  <td>{stat.stats.FGA}</td>
                  <td>{stat.stats.FG_PCT}</td>
                  <td>{stat.stats.FG3M}</td>
                  <td>{stat.stats.FG3A}</td>
                  <td>{stat.stats.FG3_PCT}</td>
                  <td>{stat.stats.FTM}</td>
                  <td>{stat.stats.FTA}</td>
                  <td>{stat.stats.FT_PCT}</td>
                  <td>{stat.stats.OREB}</td>
                  <td>{stat.stats.DREB}</td>
                  <td>{stat.stats.REB}</td>
                  <td>{stat.stats.AST}</td>
                  <td>{stat.stats.STL}</td>
                  <td>{stat.stats.BLK}</td>
                  <td>{stat.stats.TO}</td>
                  <td>{stat.stats.PF}</td>
                  <td>{stat.stats.PTS}</td>
                  <td>{stat.stats.PLUS_MINUS}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>No stats available for this player this season.</p>
      )}
    </div>
  );
};

export default PlayerDetail;
