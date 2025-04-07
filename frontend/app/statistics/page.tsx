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
}

const CURRENT_SEASON = "2024-25";

const TeamStats: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [showCurrentSeasonOnly, setShowCurrentSeasonOnly] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/teams/")
      .then((res) => res.json())
      .then((data) => {
        const sorted = [...data].sort(
          (a, b) => parseInt(b.season_year) - parseInt(a.season_year)
        );
        setTeams(sorted);
        setFilteredTeams(
          sorted.filter((team) => team.season_year === CURRENT_SEASON)
        );
      })
      .catch((err) => console.error("Error fetching team data:", err));
  }, []);

  const handleFilterChange = () => {
    const next = !showCurrentSeasonOnly;
    setShowCurrentSeasonOnly(next);
    setFilteredTeams(
      next
        ? teams.filter((team) => team.season_year === CURRENT_SEASON)
        : teams
    );
  };

  const getTeamLogoUrl = (team_id: number) =>
    `https://cdn.nba.com/logos/nba/${team_id}/global/L/logo.svg`;

  return (
    <div style={{ paddingTop: "120px" }}>
      <div className={styles.container}>
        <h2 className={styles.title}>NBA Teams by Season</h2>

        <div className={styles.filter}>
          <label>
            <input
              type="checkbox"
              checked={showCurrentSeasonOnly}
              onChange={handleFilterChange}
            />
            Show only 2024-25 season
          </label>
        </div>

        <div className={styles.grid}>
          {filteredTeams.map((team) => (
            <Link
              key={team.team_id + team.season_year}
              href="/player_stats"
              className={styles.cardLink}
            >
              <div className={styles.card}>
                <div className={styles.imagePlaceholder}>
                  <img
                    src={getTeamLogoUrl(team.team_id)}
                    alt={`${team.team_name} logo`}
                    onError={(e) => {
                      // (e.target as HTMLImageElement).src = "/fallback-logo.png"; // Optional fallback image
                    }}
                  />
                </div>
                <div className={styles.info}>
                  <p className={styles.abbreviation}>
                    {team.team_abbreviation}
                  </p>
                  <p className={styles.teamLocation}>{team.team_location}</p>
                  <p className={styles.teamName}>{team.team_name}</p>
                  <p className={styles.seasonYear}>Season: {team.season_year}</p>
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
