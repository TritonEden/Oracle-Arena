
"use client";

import { useEffect, useState } from "react";
import styles from "./gameTable.module.css";

// Define TypeScript interface for game data
interface Game {
  startTime: number;
  homeTeamLogoID: string;
  homeTeamCity: string
  homeTeamName: string;
  awayTeamLogoID: string;
  awayTeamCity: string;
  awayTeamName: string;
  predictedWinner: string;
  actualWinner: string;
  predictedTotal: string;
  actualTotal: string;
}

const GameTable: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/presentGameSummary/")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setGames(data);
      })
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

        {/* Table Body */}
        {games.length > 0 ? (
          games.map((game, index) => (
            <div key={index}>
              <div className={styles.gameRow}>
                <div className={styles.tableCell}>
                  <img src={`https://cdn.nba.com/logos/nba/${game.awayTeamLogoID}/primary/D/logo.svg`} alt={game.awayTeamName} className={styles.logo} />
                </div>
                <div className={`${styles.tableCell} ${styles.awayTeam}`}>
                  <div className={styles.teamName}>
                    <div>{game.awayTeamCity}</div>
                    <div>{game.awayTeamName}</div>
                  </div>
                </div>
                <div className={styles.tableCell}>{game.startTime}</div>
                <div className={`${styles.tableCell} ${styles.homeTeam}`}>
                  <div className={styles.teamName}>
                    <div>{game.homeTeamCity}</div>
                    <div>{game.homeTeamName}</div>
                  </div>
                </div>
                <div className={styles.tableCell}>
                  <img src={`https://cdn.nba.com/logos/nba/${game.homeTeamLogoID}/primary/D/logo.svg`} alt={game.homeTeamName} className={styles.logo} />
                </div>
              </div>

              {/* Prediction Data Row */}
              <div className={styles.dataLabelRow}>
                <div className={styles.tableCell}>Winner</div>
                <div className={styles.tableCell}>Total Score</div>
              </div>
              <div className={styles.dataRow}>
                <div className={`${styles.tableCell} ${styles.actualData}`}>Prediction</div>
                <div className={`${styles.tableCell} ${styles.predictData}`}>Actual</div>
                <div className={`${styles.tableCell} ${styles.actualData}`}>Prediction</div>
                <div className={`${styles.tableCell} ${styles.predictData}`}>Actual</div>
              </div>
              <div className={`${styles.dataRow} ${styles.displayData}`}>
                <div className={`${styles.tableCell} ${styles.actualData}`}>{game.predictedWinner}</div>
                <div className={`${styles.tableCell} ${styles.predictData}`}>{game.actualWinner}</div>
                <div className={`${styles.tableCell} ${styles.actualData}`}>{game.predictedTotal}</div>
                <div className={`${styles.tableCell} ${styles.predictData}`}>{game.actualTotal}</div>
              </div>
            </div>
          ))
        ) : (
          <div className={styles.noData}>No game data available.</div>
        )}
      </div>
    </div>
  );
};

export default GameTable;
