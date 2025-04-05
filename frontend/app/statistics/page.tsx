"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./teams.module.css";

interface Team {
  team_id: number;
  team_location: string;
  team_name: string;
  team_abbreviation: string;
  season_year: string;
  team_photo_url?: string | null;
}

const TeamStats: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/teams/")
      .then((res) => res.json())
      .then((data) => {
        // Sort by season_year descending (most recent first)
        const sorted = [...data].sort(
          (a, b) => parseInt(b.season_year) - parseInt(a.season_year)
        );
        setTeams(sorted);
      })
      .catch((err) => console.error("Error fetching team data:", err));
  }, []);

  return (
    <div style={{ paddingTop: "120px" }}>
      <div className={styles.container}>
        <h2 className={styles.title}>NBA Teams by Season</h2>
        <div className={styles.grid}>
          {teams.map((team) => (
            <Link
              key={team.team_id + team.season_year}
              href="/player_stats" // Redirect to all players for now
              className={styles.cardLink}
            >
              <div className={styles.card}>
                <div className={styles.imagePlaceholder}>
                  {team.team_photo_url ? (
                    <img src={team.team_photo_url} alt={`${team.team_name}`} />
                  ) : (
                    "No Team Image"
                  )}
                </div>
                <div className={styles.info}>
                  <h3>
                    {team.team_location} ({team.team_abbreviation})
                  </h3>
                  <p>{team.team_name}</p>
                  <p>Season: {team.season_year}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeamStats;
