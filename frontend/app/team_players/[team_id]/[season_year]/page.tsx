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

  const convertToMinutes = (time: string): number => {
    const [minutes, seconds] = time.split(":").map((str) => parseFloat(str));
    return minutes + seconds / 60;
  };

  useEffect(() => {
    if (team_id && season_year) {
      // Check local storage for cached players data
      const cachedPlayers = localStorage.getItem(`players-${team_id}-${season_year}`);
      if (cachedPlayers) {
        setPlayers(JSON.parse(cachedPlayers));
        setLoadingPlayers(false);
      } else {
        fetch(`http://localhost:8000/api/players_from_team/${team_id}/${season_year}/`)
          .then((res) => res.json())
          .then(async (data) => {
            const enrichedPlayers = await Promise.all(
              data.map(async (player: Player) => {
                try {
                  const res = await fetch(
                    `http://localhost:8000/api/player_stats_for_season/${player.player_id}/${season_year}/`
                  );
                  const stats = await res.json();
                  const uniqueGames = new Set<string>();
                  let totalMinutes = 0;
                  let gamesPlayed = 0;

                  for (const stat of stats) {
                    const parsed = JSON.parse(stat.player_game_stats);
                    const allZero = Object.values(parsed).every(
                      (val) => val === 0 || val === null || val === ""
                    );
                    if (stat.game_id.startsWith("2") && !allZero) {
                      uniqueGames.add(stat.game_id);
                      gamesPlayed += 1;
                      const minutesPlayed = convertToMinutes(parsed.MIN);
                      totalMinutes += minutesPlayed;
                    }
                  }

                  const avgMinutes = totalMinutes / Math.max(gamesPlayed, 1);
                  const maxGameMinutes = 48; 
                  const fieldTimePct = avgMinutes / maxGameMinutes;
                  return {
                    ...player,
                    gamesPlayed,
                    fieldTimePct,
                    popularityScore: gamesPlayed * fieldTimePct,
                  };
                } catch (err) {
                  console.error(`Error fetching stats for player ${player.player_id}`, err);
                  return {
                    ...player,
                    gamesPlayed: 0,
                    fieldTimePct: 0,
                    popularityScore: 0,
                  };
                }
              })
            );

            enrichedPlayers.sort((a, b) => b.popularityScore - a.popularityScore);
            setPlayers(enrichedPlayers);
            localStorage.setItem(`players-${team_id}-${season_year}`, JSON.stringify(enrichedPlayers)); // Cache data
          })
          .finally(() => setLoadingPlayers(false));
      }

      // Check local storage for cached team data
      const cachedTeam = localStorage.getItem(`team-${team_id}-${season_year}`);
      if (cachedTeam) {
        setTeam(JSON.parse(cachedTeam));
        setLoadingTeam(false);
      } else {
        fetch("http://localhost:8000/api/teams/")
          .then((res) => res.json())
          .then((data) => {
            const matched = data.find(
              (t: Team) => t.team_id.toString() === team_id && t.season_year === season_year
            );
            setTeam(matched || null);
            localStorage.setItem(`team-${team_id}-${season_year}`, JSON.stringify(matched || null)); // Cache team data
          })
          .finally(() => setLoadingTeam(false));
      }
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
