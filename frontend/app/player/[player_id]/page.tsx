"use client";

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import styles from "./playerDetail.module.css";

interface PlayerGameStats {
  game_id: string;
  stats: {
    MIN: string;
    FGM: number;
    FGA: number;
    FG_PCT: number;
    FG3M: number;
    FG3A: number;
    FG3_PCT: number;
    FTM: number;
    FTA: number;
    FT_PCT: number;
    OREB: number;
    DREB: number;
    REB: number;
    AST: number;
    STL: number;
    BLK: number;
    TO: number;
    PF: number;
    PTS: number;
    PLUS_MINUS: number;
  };
}

const PlayerDetail: React.FC = () => {
  const { player_id } = useParams();
  const searchParams = useSearchParams();
  const season_year = searchParams.get("season") ?? "2024-25";

  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/player_stats_for_season/${player_id}/${season_year}/`)
      .then((response) => response.json())
      .then((data) => {
        const parsedStats: PlayerGameStats[] = data.map((entry: any) => ({
          game_id: entry.game_id,
          stats: JSON.parse(entry.player_game_stats),
        }));

        const sorted = parsedStats.sort((a, b) => b.game_id.localeCompare(a.game_id));
        setStats(sorted);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching player season stats:", error);
        setLoading(false);
      });
  }, [player_id, season_year]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.back}>
          <button className={styles.backButton}>
            <span>&lt;</span> Back to Players
          </button>
        </div>
        <h2>Player {player_id} - Stats for {season_year}</h2>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : stats.length > 0 ? (
        <div className={styles.statsTable}>
          <table className={styles.statsTableContainer}>
            <thead>
              <tr>
                <th>Game ID</th>
                <th>MIN</th>
                <th>FGM</th>
                <th>FGA</th>
                <th>FG%</th>
                <th>FG3M</th>
                <th>FG3A</th>
                <th>FG3%</th>
                <th>FTM</th>
                <th>FTA</th>
                <th>FT%</th>
                <th>OREB</th>
                <th>DREB</th>
                <th>REB</th>
                <th>AST</th>
                <th>STL</th>
                <th>BLK</th>
                <th>TO</th>
                <th>PF</th>
                <th>PTS</th>
                <th>+/-</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((stat) => (
                <tr key={stat.game_id}>
                  <td>{stat.game_id}</td>
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
