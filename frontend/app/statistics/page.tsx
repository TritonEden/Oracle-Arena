"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./statistics.module.css";

interface Player {
  player_id: number;
  player_first_name: string;
  player_last_name: string;
  team_name: string;
  // Add an image URL if available
  image_url?: string;
}

const PlayerStats: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);

  // Fetch the list of players from the CSV
  useEffect(() => {
    fetch("http://localhost:8000/api/player_stats")
      .then((response) => response.json())
      .then((data) => setPlayers(data))
      .catch((error) => console.error("Error fetching player data:", error));
  }, []);

  return (
    <div style={{ paddingTop: "120px" }}>
      <div className={styles.container}>
        <h2 className={styles.title}>Player Stats</h2>
        <div className={styles.grid}>
          {players.map((player) => (
            <Link
              key={player.player_id}
              href={`/player/${player.player_id}`}
              className={styles.cardLink}
            >
              <div className={styles.card}>
                {/* Display player image if available, else a placeholder */}
                <div className={styles.imagePlaceholder}>
                  {player.image_url ? (
                    <img src={player.image_url} alt={`${player.player_first_name} ${player.player_last_name}`} />
                  ) : (
                    "No Image"
                  )}
                </div>
                <div className={styles.info}>
                  <h3>
                    {player.player_first_name} {player.player_last_name}
                  </h3>
                  <p>Team: {player.team_name}</p>
                  <p>ID: {player.player_id}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlayerStats;
