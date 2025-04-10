"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import styles from "./teamPlayers.module.css";

interface Player {
  player_id: string;
  full_name: string;
}

const TeamPlayersPage: React.FC = () => {
  const { team_id, season_year } = useParams();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/players_from_team/${team_id}/${season_year}/`)
      .then((res) => res.json())
      .then((data) => {
        setPlayers(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching players:", err);
        setLoading(false);
      });
  }, [team_id, season_year]);

  return (
    <div style={{ paddingTop: "100px" }}>
      <h2>Players for Team {team_id} - {season_year}</h2>
      {loading ? (
        <p>Loading players...</p>
      ) : players.length === 0 ? (
        <p>No players found for this team in this season.</p>
      ) : (
        <div className={styles.playerGrid}>
          {players.map((player) => (
            <Link
              key={player.player_id}
              href={`/player/${player.player_id}?season=${season_year}`}
              className={styles.cardLink}
            >
              <div className={styles.playerCard}>
                <h3>{player.full_name}</h3>
                <p>ID: {player.player_id}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default TeamPlayersPage;
