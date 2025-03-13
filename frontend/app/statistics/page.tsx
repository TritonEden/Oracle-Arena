"use client";

import { useEffect, useState } from "react";
import styles from "./Statistics.module.css"; // Import the CSS module

// Define TypeScript interface for player data
interface Player {
  id: number;
  name: string;
  team_name: string;
  image_url: string;  // URL for player's image
  points_per_game: number;
  assists: number;
  rebounds: number;
  field_goal_percentage: number;
  three_point_percentage: number;
  free_throw_percentage: number;
}

const Statistics: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/player_stats/")  // API URL for player stats
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        const players = data.map((player: any) => {
          const stats = JSON.parse(player.player_game_stats)[0];
          return {
            id: player.id,
            name: player.player_id,  // Assuming player_id is used for name; update as necessary
            points_per_game: stats.PTS,
            team_name: player.team_id,  // Assuming team_id is used for team name; update as necessary
            assists: stats.AST,
            rebounds: stats.REB,
            field_goal_percentage: stats.FG_PCT,
            three_point_percentage: stats.FG3_PCT,
            free_throw_percentage: stats.FT_PCT
          };
        });
        setPlayers(players);
      })
      .catch((error) => console.error("Error fetching player data:", error));
  }, []);

  return (
    <div className={`${styles.container} ${styles.statsPage}`}>
      <div className={styles.playersTable}>
        {/* Header Row */}
        <div className={styles.headerRow}>
          <div className={styles.tableHeader}>Player</div>
          <div className={styles.tableHeader}>Team</div>
          <div className={styles.tableHeader}>Points Per Game</div>
          <div className={styles.tableHeader}>Assists</div>
          <div className={styles.tableHeader}>Rebounds</div>
          <div className={styles.tableHeader}>Field Goal %</div>
          <div className={styles.tableHeader}>3P %</div>
          <div className={styles.tableHeader}>Free Throw %</div>
        </div>

        {/* Table Body */}
        {players.length > 0 ? (
          players.map((player) => (
            <div key={player.id} className={styles.playerRow}>
              <div className={styles.tableCell}>{player.name}</div>
              <div className={styles.tableCell}>{player.team_name}</div>
              <div className={styles.tableCell}>{player.points_per_game.toFixed(2)}</div>
              <div className={styles.tableCell}>{player.assists.toFixed(2)}</div>
              <div className={styles.tableCell}>{player.rebounds.toFixed(2)}</div>
              <div className={styles.tableCell}>{(player.field_goal_percentage * 100).toFixed(2)}%</div>
              <div className={styles.tableCell}>{(player.three_point_percentage * 100).toFixed(2)}%</div>
              <div className={styles.tableCell}>{(player.free_throw_percentage * 100).toFixed(2)}%</div>
            </div>
          ))
        ) : (
          <div className={styles.noData}>No player data available.</div>
        )}
      </div>
    </div>
  );
};

export default Statistics;
