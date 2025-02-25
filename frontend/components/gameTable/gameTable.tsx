"use client";

import { useEffect, useState } from "react";
import styles from "./gameTable.module.css";

// Define TypeScript interface for game data
interface Game {
  team_1_logo: string;
  team_1_name: string;
  start_time: number;
  team_2_name: string;
  team_2_logo: string;
}

const GameTable: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);

  useEffect(() => {
    fetch("http://localhost:3000/gamesummary/")
      .then((response) => response.json())
      .then((data: Game[]) => setGames(data))
      .catch((error) => console.error("Error fetching game summary:", error));
  }, []);

  return (
    <div className={styles.tableContainer}>
      <div className={styles.gamesTable}>
        {/* Header Row */}
        <div className={styles.headerRow}>
          <div>Visiting Team</div>
          <div>at</div>
          <div>Home Team</div>
        </div>

        {/* Table Body - Dynamically Generated */}
        {games.map((game, index) => (
          <div key={index}>
            <div className={styles.gameRow}>
              <div className={styles.tableCell}>
                <img src={game.team_1_logo} alt={game.team_1_name} className={styles.logo} />
              </div>
              <div className={styles.tableCell}>{game.team_1_name}</div>
              <div className={styles.tableCell}>{game.start_time}:00</div>
              <div className={styles.tableCell}>{game.team_2_name}</div>
              <div className={styles.tableCell}>
                <img src={game.team_2_logo} alt={game.team_2_name} className={styles.logo} />
              </div>
            </div>

            {/* Prediction Data Row */}
            <div className={styles.dataLabelRow}>
              <div className={styles.tableCell}>Winner (Prediction vs Actual)</div>
              <div className={styles.tableCell}>Total Score (Prediction vs Actual)</div>
            </div>
            <div className={styles.dataRow}>
              <div className={`${styles.tableCell} ${styles.actualData}`}>Pred. Winner</div>
              <div className={`${styles.tableCell} ${styles.predictData}`}>Act. Winner</div>
              <div className={`${styles.tableCell} ${styles.actualData}`}>Pred. Total</div>
              <div className={`${styles.tableCell} ${styles.predictData}`}>Act. Total</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GameTable;
