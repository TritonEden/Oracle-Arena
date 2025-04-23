"use client";

import { useEffect, useState } from "react";
import styles from "./gameTable.module.css";

interface Game {
  startTime: number;
  homeTeamLogoID: string;
  homeTeamCity: string;
  homeTeamName: string;
  homeTeamAbbreviation: string;
  awayTeamLogoID: string;
  awayTeamCity: string;
  awayTeamName: string;
  awayTeamAbbreviation: string;
  predictedWinner: string;
  actualWinner: string;
  predictedTotal: string;
  actualTotal: string;
}

interface GameTableProps {
  selectedDate: Date;
}

const GameTable: React.FC<GameTableProps> = ({ selectedDate }) => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const getCacheKey = (date: Date) => `gamesData_${date.toISOString().split("T")[0]}`;

  useEffect(() => {
    const fetchGames = async () => {
      const sqlDate = selectedDate.toISOString().split("T")[0];
      const cacheKey = getCacheKey(selectedDate);

      // Try getting cached data
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          setGames(parsed);
          setLoading(false);
          return;
        } catch (err) {
          console.warn("Corrupt cache, refetching from API...");
          localStorage.removeItem(cacheKey);
        }
      }

      // If no cache, fetch from API
      setLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/home_away_team_info_on_date/${sqlDate}`
        );
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setGames(data);
        localStorage.setItem(cacheKey, JSON.stringify(data)); // Cache result
      } catch (error) {
        console.error("Error fetching game summary:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchGames();
  }, [selectedDate]);

  if (loading) {
    return <div className={styles.loading}>Loading Games ...</div>;
  }

  return (
    <div className={styles.tableContainer}>
      <div className={styles.gamesTable}>
        {games.length > 0 ? (
          <>
            <div className={styles.headerRow}>
              <div>Visiting Team</div>
              <div>at</div>
              <div>Home Team</div>
            </div>
            {games.map((game, index) => (
              <div key={index}>
                <div className={styles.gameRow}>
                  <div className={styles.tableCell}>
                    <img
                      src={`https://cdn.nba.com/logos/nba/${game.awayTeamLogoID}/primary/D/logo.svg`}
                      alt={game.awayTeamName}
                      className={styles.logo}
                    />
                  </div>
                  <div className={`${styles.tableCell} ${styles.awayTeam}`}>
                    <div className={styles.teamName}>
                      <div>{game.awayTeamCity}</div>
                      <div>{game.awayTeamName}</div>
                    </div>
                    <div className={styles.teamAbbreviation}>
                      {game.awayTeamAbbreviation}
                    </div>
                  </div>
                  <div className={styles.tableCell}>{game.startTime}</div>
                  <div className={`${styles.tableCell} ${styles.homeTeam}`}>
                    <div className={styles.teamName}>
                      <div>{game.homeTeamCity}</div>
                      <div>{game.homeTeamName}</div>
                    </div>
                    <div className={styles.teamAbbreviation}>
                      {game.homeTeamAbbreviation}
                    </div>
                  </div>
                  <div className={styles.tableCell}>
                    <img
                      src={`https://cdn.nba.com/logos/nba/${game.homeTeamLogoID}/primary/D/logo.svg`}
                      alt={game.homeTeamName}
                      className={styles.logo}
                    />
                  </div>
                </div>
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
            ))}
          </>
        ) : (
          <div className={styles.noData}>No game data available.</div>
        )}
      </div>
    </div>
  );
};

export default GameTable;
