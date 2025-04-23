"use client";

import { useEffect, useState } from "react";
import styles from "./gameTable.module.css";

interface Game {
  startTime: number;
  homeTeamID: number;
  homeTeamLogoID: string;
  homeTeamCity: string;
  homeTeamName: string;
  homeTeamAbbreviation: string;
  homeTeamScore: number;
  awayTeamID: number;
  awayTeamLogoID: string;
  awayTeamCity: string;
  awayTeamName: string;
  awayTeamAbbreviation: string;
  awayTeamScore: number;
  predictedWinner: string;
  actualWinner: string;
  predictedTotal: number;
  actualTotal: number;
}

interface GameTableProps {
  selectedDate: Date;
}

const GameTable: React.FC<GameTableProps> = ({ selectedDate }) => {
  const [games, setGames] = useState<Game[]>([]);
  const [winLossRecords, setWinLossRecords] = useState<{ [teamId: number]: string }>({});
  const [loading, setLoading] = useState<boolean>(true);

  const fetchWinLoss = async (teamId: number, seasonYear: string): Promise<string> => {
    try {
      const response = await fetch(`http://localhost:8000/api/wins_losses/${teamId}/${seasonYear}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching W-L for team ${teamId}:`, error);
      return "--";
    }
  };

  const getCacheKey = (date: Date) => `gamesData_${date.toISOString().split("T")[0]}`;

  useEffect(() => {
    const fetchGames = async () => {
      const sqlDate = selectedDate.toISOString().split("T")[0];
      const seasonYear = selectedDate.getFullYear().toString();

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
        const data: Game[] = await response.json();
        setGames(data);
        localStorage.setItem(cacheKey, JSON.stringify(data)); // Cache result

        const newWinLoss: { [teamId: number]: string } = {};
        for (const game of data) {
          const { homeTeamID, awayTeamID } = game;

          if (!newWinLoss[homeTeamID]) {
            newWinLoss[homeTeamID] = await fetchWinLoss(homeTeamID, seasonYear);
          }
          if (!newWinLoss[awayTeamID]) {
            newWinLoss[awayTeamID] = await fetchWinLoss(awayTeamID, seasonYear);
          }
        }

        setWinLossRecords(newWinLoss);
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
                    <div className={styles.awayTeamInfo}>
                      <div className={styles.teamName}>
                        <div>{game.awayTeamCity}</div>
                        <div>{game.awayTeamName}</div>
                      </div>
                      <div className={styles.teamAbbreviation}>{game.awayTeamAbbreviation}</div>
                      <div className={styles.WLRecord}>{winLossRecords[game.awayTeamID]}</div>
                    </div>
                  </div>
                  <div className={styles.timeAndScore}>
                    <div className={styles.tableCell}>{game.startTime}</div>
                    <div className={styles.score}>{game.awayTeamScore} - {game.homeTeamScore}</div>
                  </div>
                  <div className={`${styles.tableCell} ${styles.homeTeam}`}>
                    <div className={styles.homeTeamInfo}>
                      <div className={styles.teamName}>
                        <div>{game.homeTeamCity}</div>
                        <div>{game.homeTeamName}</div>
                      </div>
                      <div className={styles.teamAbbreviation}>{game.homeTeamAbbreviation}</div>
                      <div className={styles.WLRecord}>{winLossRecords[game.homeTeamID]}</div>
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
