"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./teams.module.css";

// Performance logging utility
const logPerformance = async (label: string, operation: () => Promise<any>) => {
  console.log(`Starting: ${label}...`);
  const startTime = performance.now();
  try {
    const result = await operation();
    const endTime = performance.now();
    console.log(`${label} completed in ${((endTime - startTime) / 1000).toFixed(2)} seconds`);
    return result;
  } catch (error) {
    const endTime = performance.now();
    console.error(`${label} failed after ${((endTime - startTime) / 1000).toFixed(2)} seconds:`, error);
    throw error;
  }
};

interface Team {
  team_id: number;
  team_location: string;
  team_name: string;
  team_abbreviation: string;
  season_year: string;
}

const TeamStats: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [showCurrentSeasonOnly, setShowCurrentSeasonOnly] = useState(true);
  const [currentSeason, setCurrentSeason] = useState<string>("2024-25");

  useEffect(() => {
    logPerformance("Fetch current season", async () => {
      const res = await fetch("http://localhost:8000/api/get_current_season");
      const data = await res.json();
      setCurrentSeason(data.current_season);
    }).catch((err) => console.error("Failed to fetch current season", err));
  }, []);

  useEffect(() => {
    // Check if cached data exists in sessionStorage
    const cachedData = sessionStorage.getItem("teamsData");
    if (cachedData) {
      // Parse and use the cached data
      const data = JSON.parse(cachedData);
      const sorted = [...data].sort(
        (a, b) => parseInt(b.season_year) - parseInt(a.season_year)
      );
      setTeams(sorted);
      setFilteredTeams(
        sorted.filter((team) => team.season_year === currentSeason)
      );
    } else {
      // If no cached data, fetch from API
      logPerformance("Fetch teams data", async () => {
        const res = await fetch("http://localhost:8000/api/teams/");
        const data = await res.json();
        const sorted = [...data].sort(
          (a, b) => parseInt(b.season_year) - parseInt(a.season_year)
        );
        setTeams(sorted);
        setFilteredTeams(
          sorted.filter((team) => team.season_year === currentSeason)
        );
        // Cache the fetched data in sessionStorage
        sessionStorage.setItem("teamsData", JSON.stringify(data));
      }).catch((err) => console.error("Error fetching team data:", err));
    }
  }, [currentSeason]);

  const handleFilterChange = () => {
    const next = !showCurrentSeasonOnly;
    setShowCurrentSeasonOnly(next);
    setFilteredTeams(
      next
        ? teams.filter((team) => team.season_year === currentSeason)
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
            Show only {currentSeason} season
          </label>
        </div>

        <div className={styles.grid}>
          {filteredTeams.map((team) => (
            <Link
              key={team.team_id + team.season_year}
              href={`/team_players/${team.team_id}/${team.season_year}`}
              className={styles.cardLink}
            >
              <div className={styles.card}>
                <div className={styles.imagePlaceholder}>
                <img
                  src={getTeamLogoUrl(team.team_id)}
                  alt={`${team.team_name} logo`}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = "/images/logo.png";
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
