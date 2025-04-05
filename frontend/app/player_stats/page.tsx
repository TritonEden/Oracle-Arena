"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./player.module.css";

interface Player {
  player_id: number;
  first_name: string;
  last_name: string;
  player_photo_url?: string;
}

const PlayerStats: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/player_stats/")
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
                <div className={styles.imagePlaceholder}>
                  {player.player_photo_url ? (
                    <img
                      src={player.player_photo_url}
                      alt={`${player.first_name} ${player.last_name}`}
                    />
                  ) : (
                    "No Image"
                  )}
                </div>
                <div className={styles.info}>
                  <h3>
                    {player.first_name} {player.last_name}
                  </h3>
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
