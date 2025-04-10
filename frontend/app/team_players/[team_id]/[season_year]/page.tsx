"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import styles from "./teamplayers.module.css";
import Link from "next/link";

interface Player {
  player_id: number;
  first_name: string;
  last_name: string;
  player_photo_url?: string;
}

interface Team {
  team_id: number;
  team_location: string;
  team_name: string;
  season_year: string;
}

const TeamPlayersPage: React.FC = () => {
  const params = useParams();
  const team_id = params?.team_id as string;
  const season_year = params?.season_year as string;

  const [players, setPlayers] = useState<Player[]>([]);
  const [team, setTeam] = useState<Team | null>(null);

  useEffect(() => {
    if (team_id && season_year) {
      // Fetch players from the team
      fetch(`http://localhost:8000/api/players_from_team/${team_id}/${season_year}/`)
        .then((res) => res.json())
        .then((data) => setPlayers(data))
        .catch((err) => console.error("Error fetching players:", err));

      // Fetch all teams and find the one matching team_id and season_year
      fetch("http://localhost:8000/api/teams/")
        .then((res) => res.json())
        .then((data) => {
          const matched = data.find(
            (t: Team) =>
              t.team_id.toString() === team_id &&
              t.season_year === season_year
          );
          setTeam(matched || null);
        })
        .catch((err) => console.error("Error fetching team data:", err));
    }
  }, [team_id, season_year]);

  const teamTitle = team
    ? `${team.team_location} ${team.team_name} (${team.season_year})`
    : `Team ${team_id} - Season ${season_year}`;

  return (
    <div style={{ paddingTop: "130px" }}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.back}>
            <button className={styles.backButton}>
              <span>&lt;</span> Back to Teams
            </button>
          </div>
          <h2 className={styles.title}>{teamTitle}</h2>
        </div>

        <div className={styles.grid}>
          {players.length === 0 ? (
            <p>No players found.</p>
          ) : (
            players.map((player) => (
              <Link
                key={player.player_id}
                href={`/player/${player.player_id}?season=${season_year}`}  // Include season as a query parameter
                className={styles.cardLink}
              >
                <div className={styles.card}>
                  <div className={styles.imagePlaceholder}>
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                      alt={`${player.first_name} ${player.last_name}`}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = "/fallback-player.png";
                      }}
                    />
                  </div>
                  <div className={styles.info}>
                    <h3>{player.first_name} {player.last_name}</h3>
                    <p>ID: {player.player_id}</p>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamPlayersPage;
