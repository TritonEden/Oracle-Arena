"use client";

import { useEffect, useState } from "react";
import styles from "./Statistics.module.css"; // Import the CSS module

// Define TypeScript interface for player data
interface Player {
  id: number;
  name: string;
  points_per_game: number;
  team_name: string;
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
        setPlayers(data);
      })
      .catch((error) => console.error("Error fetching player data:", error));
  }, []);

  return (
    <div className={styles.tableContainer}>
      <div className={styles.playersTable}>
        {/* Header Row */}
        <div className={styles.headerRow}>
          <div>Player</div>
          <div>Team</div>
          <div>Points Per Game</div>
        </div>

        {/* Table Body */}
        {players.length > 0 ? (
          players.map((player) => (
            <div key={player.id} className={styles.playerRow}>
              <div className={styles.tableCell}>{player.name}</div>
              <div className={styles.tableCell}>{player.team_name}</div>
              <div className={styles.tableCell}>{player.points_per_game.toFixed(2)}</div>
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
