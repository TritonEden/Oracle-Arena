"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import styles from "./playerDetail.module.css";

interface PlayerGameStats {
  game_id: string;
  team_id: string;
  stats: {
    MIN: string;
    FGM: string;
    FGA: string;
    FG_PCT: string;
    FG3M: string;
    FG3A: string;
    FG3_PCT: string;
    FTM: string;
    FTA: string;
    FT_PCT: string;
    OREB: string;
    DREB: string;
    REB: string;
    AST: string;
    STL: string;
    BLK: string;
    TO: string;
    PF: string;
    PTS: string;
    PLUS_MINUS: string;
  };
}

const PlayerDetail: React.FC = () => {
  const { player_id } = useParams();
  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/player_game_stats/${player_id}`)
      .then((response) => response.json())
      .then((data) => {
        // Log the raw data to check its structure
        console.log("API Response Data:", data);

        const parsedStats = data.map((stat: any) => {
          let parsedStatsArray = stat.stats && stat.stats.length > 0 ? stat.stats : [{
            MIN: 'N/A', FGM: 'N/A', FGA: 'N/A', FG_PCT: 'N/A', FG3M: 'N/A', FG3A: 'N/A', FG3_PCT: 'N/A',
            FTM: 'N/A', FTA: 'N/A', FT_PCT: 'N/A', OREB: 'N/A', DREB: 'N/A', REB: 'N/A', AST: 'N/A',
            STL: 'N/A', BLK: 'N/A', TO: 'N/A', PF: 'N/A', PTS: 'N/A', PLUS_MINUS: 'N/A'
          }];

          console.log("Parsed Stats Array:", parsedStatsArray);

          return {
            ...stat,
            stats: parsedStatsArray[0], // Take the first element if the array is not empty
          };
        });
        setStats(parsedStats);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching player stats:", error);
        setLoading(false);
      });
  }, [player_id]);

  return (
    <div style={{ paddingTop: "120px" }}>
      <h2>Player Stats</h2>
      {loading ? (
        <p>Loading...</p>
      ) : stats.length > 0 ? (
        <div className={styles.statsTable}>
          <h3>Game Stats for Player {player_id}</h3>
          <table className={styles.statsTableContainer}>
            <thead>
              <tr>
                <th>Game ID</th>
                <th>Team ID</th>
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
                  <td>{stat.team_id}</td>
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
        <p>No stats available for this player.</p>
      )}
    </div>
  );
};

export default PlayerDetail;
