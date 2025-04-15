"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
  const router = useRouter();
  const params = useParams();
  const team_id = params?.team_id as string;
  const season_year = params?.season_year as string;

  const [players, setPlayers] = useState<Player[]>([]);
  const [team, setTeam] = useState<Team | null>(null);
  const [loadingPlayers, setLoadingPlayers] = useState(true);
  const [loadingTeam, setLoadingTeam] = useState(true);

  useEffect(() => {
    if (team_id && season_year) {
      fetch(`http://localhost:8000/api/players_from_team/${team_id}/${season_year}/`)
        .then((res) => res.json())
        .then((data) => setPlayers(data))
        .finally(() => setLoadingPlayers(false));

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
        .finally(() => setLoadingTeam(false));
    }
  }, [team_id, season_year]);

  const isLoading = loadingPlayers || loadingTeam;

  const teamTitle = team
    ? `${team.team_location} ${team.team_name} (${team.season_year})`
    : `Team ${team_id} - Season ${season_year}`;

  return (
    <div style={{ paddingTop: "130px" }}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.back}>
            <button
              className={styles.backButton}
              onClick={() => router.push("/statistics")}
            >
              <span>&lt;</span> Back to Teams
            </button>
          </div>
          <h2 className={styles.title}>{isLoading ? "Loading..." : teamTitle}</h2>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : players.length === 0 ? (
          <p>No players found.</p>
        ) : (
          <div className={styles.grid}>
            {players.map((player) => (
              <Link
                key={player.player_id}
                href={`/player/${player.player_id}?season=${season_year}&team_id=${team_id}`}
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
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamPlayersPage;
