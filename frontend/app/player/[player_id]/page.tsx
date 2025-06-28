"use client";

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import styles from "./playerDetail.module.css";

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

interface PlayerGameStats {
  game_id: string;
  game_date: string;
  stats: { [key: string]: any };
}

interface AverageStats {
  season: string;
  stats: { [key: string]: number };
}

const overUnderOptions = [
  { label: "PTS", key: "PTS" },
  { label: "3-PT Made", key: "FG3M" },
  { label: "REB", key: "REB" },
  { label: "AST", key: "AST" },
  { label: "FGM", key: "FGM" },
  { label: "DREB", key: "DREB" },
  { label: "REB+AST", key: "REB+AST" },
  { label: "PTS+REB+AST", key: "PTS+REB+AST" },
];

const PlayerDetail: React.FC = () => {
  const { player_id } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [currentSeason, setCurrentSeason] = useState<string>("2024-25");
  const season_year = searchParams.get("season") ?? currentSeason;
  const team_id = searchParams.get("team_id");
  const player_name = searchParams.get("player_name");

  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  const [averageStats, setAverageStats] = useState<AverageStats[]>([]);
  const [playerName, setPlayerName] = useState<string>(player_name || "");
  const [loadingStats, setLoadingStats] = useState<boolean>(true);
  const [loadingAverages, setLoadingAverages] = useState<boolean>(true);

  const [currentPage, setCurrentPage] = useState(1);
  const gamesPerPage = 10;

  const [selectedStat, setSelectedStat] = useState("PTS");
  const [compareValue, setCompareValue] = useState<number | null>(null);

  console.log("PlayerDetail: Loading player", { player_id, season_year, player_name });

  const avgHeaders = (
    <tr>
      <th>Season</th>
      <th>FGM</th>
      <th>FGA</th>
      <th>FG%</th>
      <th>3PM</th>
      <th>3PA</th>
      <th>3P%</th>
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
  );

  // Function to check if we should refresh based on noon EST
  const shouldRefreshAtNoon = (lastRefreshTime: number): boolean => {
    const now = new Date();
    const lastRefresh = new Date(lastRefreshTime);
    
    // Convert to EST
    const nowEST = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
    const lastRefreshEST = new Date(lastRefresh.toLocaleString("en-US", {timeZone: "America/New_York"}));
    
    // Check if noon EST has passed since last refresh
    const noonToday = new Date(nowEST);
    noonToday.setHours(12, 0, 0, 0);
    
    return nowEST >= noonToday && lastRefreshEST < noonToday;
  };

  useEffect(() => {
    logPerformance("Fetch current season", async () => {
      const res = await fetch("http://localhost:8000/api/get_current_season");
      const data = await res.json();
      setCurrentSeason(data.current_season);
    }).catch((err) => console.error("Failed to fetch current season", err));
  }, []);

  useEffect(() => {
    if (player_name) {
      setPlayerName(player_name);
    } else {
      // Only fetch player name if not provided in URL
      const fetchPlayerName = async () => {
        try {
          const response = await fetch(`http://localhost:8000/api/player/${player_id}/`);
          if (response.ok) {
            const data = await response.json();
            setPlayerName(`${data.first_name} ${data.last_name}`);
          }
        } catch (error) {
          console.error("Error fetching player name:", error);
        }
      };
      fetchPlayerName();
    }
  }, [player_id, player_name]);

  useEffect(() => {
    const cacheKey = `playerStats-${player_id}-${season_year}`;
    const lastRefreshKey = `playerStatsLastRefresh-${player_id}-${season_year}`;
    const cachedStats = sessionStorage.getItem(cacheKey);
    const lastRefresh = sessionStorage.getItem(lastRefreshKey);

    const fetchStats = async () => {
      console.log("PlayerDetail: Fetching stats for", { player_id, season_year });
      setLoadingStats(true);
      
      if (cachedStats && lastRefresh) {
        try {
          const lastRefreshTime = parseInt(lastRefresh);
          if (!shouldRefreshAtNoon(lastRefreshTime)) {
            console.log("PlayerDetail: Using cached stats");
            setStats(JSON.parse(cachedStats));
            setLoadingStats(false);
            return;
          }
        } catch (err) {
          console.warn("Error parsing last refresh time:", err);
        }
      }

      try {
        const response = await fetch(
          `http://localhost:8000/api/player_stats_for_season/${player_id}/${season_year}/`
        );
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("PlayerDetail: Raw API data count:", data.length);
        
        // Get unique game IDs
        const gameIds = Array.from(new Set(data.map((entry: any) => entry.game_id)));
        console.log("PlayerDetail: Unique games found:", gameIds.length);
        
        // Batch fetch game dates
        const gameDates = await Promise.all(
          gameIds.map(async (gameId) => {
            try {
              const dateRes = await fetch(`http://localhost:8000/api/game/${gameId}/`);
              if (!dateRes.ok) {
                console.warn(`Failed to fetch date for game ${gameId}: ${dateRes.status}`);
                return { gameId, date: null };
              }
              const dateData = await dateRes.json();
              return { 
                gameId, 
                date: dateData[0]?.game_date ?? null 
              };
            } catch (error) {
              console.error(`Error fetching date for game ${gameId}:`, error);
              return { gameId, date: null };
            }
          })
        );
        
        // Create a map of game ID to date
        const gameDateMap = new Map(gameDates.map(gd => [gd.gameId, gd.date]));
        
        // Process the raw data to match PlayerGameStats interface
        const processedData: PlayerGameStats[] = data.map((entry: any) => {
          try {
            // Parse stats
            const stats = JSON.parse(entry.player_game_stats);
            
            // Format minutes if present
            if (stats.MIN) {
              const [minutes, seconds] = stats.MIN.split(":");
              stats.MIN = `${parseInt(minutes)}:${seconds.padStart(2, "0")}`;
            }
            
            return {
              game_id: entry.game_id,
              game_date: gameDateMap.get(entry.game_id) ?? "1970-01-01",
              stats: stats,
            };
          } catch (error) {
            console.error(`Error processing game ${entry.game_id}:`, error);
            return null;
          }
        });
        
        // Filter out null entries and empty stats
        const validData = processedData.filter(entry => entry !== null);
        
        const filteredStats = validData.filter((entry) => {
          if (!entry) return false;
          const isEmptyStats = (stats: { [key: string]: any }) =>
            !stats || Object.values(stats).every((val) => val === 0 || val === null || val === "");
          return !isEmptyStats(entry.stats);
        });
        
        console.log("PlayerDetail: Processed games:", filteredStats.length);
        
        const sortedByDate = filteredStats.sort((a: PlayerGameStats, b: PlayerGameStats) =>
          new Date(b.game_date).getTime() - new Date(a.game_date).getTime()
        );
        
        setStats(sortedByDate);
        sessionStorage.setItem(cacheKey, JSON.stringify(sortedByDate));
        sessionStorage.setItem(lastRefreshKey, Date.now().toString());
      } catch (err) {
        console.error("Error fetching player season stats:", err);
      } finally {
        setLoadingStats(false);
      }
    };

    fetchStats();
  }, [player_id, season_year]);

  useEffect(() => {
    const cacheKey = `playerAvgStats-${player_id}-${season_year}`;
    const lastRefreshKey = `playerAvgStatsLastRefresh-${player_id}-${season_year}`;
    const cachedAverages = sessionStorage.getItem(cacheKey);
    const lastRefresh = sessionStorage.getItem(lastRefreshKey);

    const years = Array.from({ length: 5 }, (_, i) => {
      const [start, end] = season_year.split("-");
      const prevStart = parseInt(start) - i;
      return `${prevStart}-${(parseInt(end) - i).toString().padStart(2, "0")}`;
    });

    if (cachedAverages && lastRefresh) {
      try {
        const lastRefreshTime = parseInt(lastRefresh);
        if (!shouldRefreshAtNoon(lastRefreshTime)) {
          setAverageStats(JSON.parse(cachedAverages));
          setLoadingAverages(false);
          return;
        }
      } catch (err) {
        console.warn("Error parsing last refresh time:", err);
      }
    }

    setLoadingAverages(true);
    logPerformance("Fetch player average stats", async () => {
      const results = await Promise.all(
        years.map((year) =>
          fetch(`http://localhost:8000/api/player_average_stats_for_season/${player_id}/${year}/`)
            .then((res) => res.json())
            .then((data) => {
              if (data.length > 0) {
                return { season: year, stats: JSON.parse(data[0].average_stats) };
              }
            })
            .catch(() => null)
        )
      );
      const validResults = results.filter((item) => item !== null) as AverageStats[];
      setAverageStats(validResults);
      sessionStorage.setItem(cacheKey, JSON.stringify(validResults));
      sessionStorage.setItem(lastRefreshKey, Date.now().toString());
    }).catch((err) => console.error("Error fetching average stats:", err))
    .finally(() => setLoadingAverages(false));
  }, [player_id, season_year]);

  const totalPages = Math.ceil(stats.length / gamesPerPage);
  const currentStats = stats.slice((currentPage - 1) * gamesPerPage, currentPage * gamesPerPage);

  const getStatValue = (s: any): number => {
    const toNum = (val: any) => Number(val ?? 0); // Helper for coercion
    
    // Handle case where s is undefined or null
    if (!s) return 0;
  
    switch (selectedStat) {
      case "REB+AST":
        return toNum(s.REB) + toNum(s.AST);
      case "PTS+REB+AST":
        return toNum(s.PTS) + toNum(s.REB) + toNum(s.AST);
      default:
        return toNum(s[selectedStat]);
    }
  };

  const getColorClass = (statVal: number) => {
    if (compareValue === null || isNaN(compareValue)) return "";
    if (statVal > compareValue) return styles.green;
    if (statVal < compareValue) return styles.red;
    return "";
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.back}>
          <button
            className={styles.backButton}
            onClick={() =>
              router.push(team_id ? `/team_players/${team_id}/${season_year}` : "/statistics")
            }
          >
            <span>&lt;</span> Back to Players
          </button>
        </div>
        <h2>{`${playerName} - Games for ${season_year}`}</h2>
      </div>

      {/* Over/Under Controls */}
      <div className={styles.formContainer}>
        <label>
          Compare:
          <select className={styles.formControl}
            value={selectedStat}
            onChange={(e) => setSelectedStat(e.target.value)}
          >
            {overUnderOptions.map((opt) => (
              <option key={opt.key} value={opt.key}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Value:
          <input type="number" className={`${styles.formControl} ${styles.numInput}`}
            value={compareValue ?? ""}
            onChange={(e) => setCompareValue(e.target.value ? parseFloat(e.target.value) : null)}
          />
        </label>
      </div>

      {/* Recent Games Table */}
      <h2 style={{ color: "#cc9a36", marginBottom: "10px" }}>Recent Games</h2>
      <div className={styles.statsTable}>
        {loadingStats ? (
          <div className={styles.loading}>Loading Player Stats...</div>
        ) : (
          <table className={styles.statsTableContainer}>
            <thead>
              <tr>
                <th>Date</th>
                <th>{selectedStat}</th>
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
              {currentStats.map((stat, index) => {
                const statVal = getStatValue(stat.stats);
                const colorClass = getColorClass(statVal);
                const isPlayoffGame = (game_id?: string): boolean => {
                  return game_id?.startsWith("4") ?? false;
                };
                return (
                  <tr key={index}>
                    <td className={stat?.game_id && isPlayoffGame(stat.game_id) ? styles.playoffDate : ""}>
                      {stat?.game_date}
                    </td>
                    <td className={colorClass}>{statVal}</td>
                    <td>{stat.stats?.MIN ?? "-"}</td>
                    <td>{stat.stats?.FGM ?? "-"}</td>
                    <td>{stat.stats?.FGA ?? "-"}</td>
                    <td>{stat.stats?.FG_PCT !== undefined ? stat.stats.FG_PCT.toFixed(3) : "-"}</td>
                    <td>{stat.stats?.FG3M ?? "-"}</td>
                    <td>{stat.stats?.FG3A ?? "-"}</td>
                    <td>{stat.stats?.FG3_PCT !== undefined ? stat.stats.FG3_PCT.toFixed(3) : "-"}</td>
                    <td>{stat.stats?.FTM ?? "-"}</td>
                    <td>{stat.stats?.FTA ?? "-"}</td>
                    <td>{stat.stats?.FT_PCT !== undefined ? stat.stats.FT_PCT.toFixed(3) : "-"}</td>
                    <td>{stat.stats?.OREB ?? "-"}</td>
                    <td>{stat.stats?.DREB ?? "-"}</td>
                    <td>{stat.stats?.REB ?? "-"}</td>
                    <td>{stat.stats?.AST ?? "-"}</td>
                    <td>{stat.stats?.STL ?? "-"}</td>
                    <td>{stat.stats?.BLK ?? "-"}</td>
                    <td>{stat.stats?.TO ?? "-"}</td>
                    <td>{stat.stats?.PF ?? "-"}</td>
                    <td>{stat.stats?.PTS ?? "-"}</td>
                    <td>{stat.stats?.PLUS_MINUS ?? "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <div className={styles.pagination}>
        <button onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))} disabled={currentPage === 1} className={styles.arrowButton}>
          &lt;
        </button>
        {Array.from({ length: totalPages }, (_, i) => (
          <button
            key={i}
            onClick={() => setCurrentPage(i + 1)}
            className={`${styles.paginationButton} ${currentPage === i + 1 ? styles.activePage : ""}`}
          >
            {i + 1}
          </button>
        ))}
        <button onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} className={styles.arrowButton}>
          &gt;
        </button>
      </div>

      {/* Season Averages Table */}
      <h2 style={{ color: "#cc9a36", marginTop: "40px", marginBottom: "10px" }}>Regular Season Averages</h2>
      <div className={styles.statsTable}>
        {loadingAverages ? (
          <div className={styles.loading}>Loading Season Averages...</div>
        ) : (
          <table className={styles.statsTableContainer}>
            <thead>{avgHeaders}</thead>
            <tbody>
              {averageStats.map((season, idx) => {
                const s = season.stats;
                return (
                  <tr key={idx}>
                    <td>{season.season}</td>
                    <td>{s?.FGM?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FGA?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FG_PCT ? s.FG_PCT.toFixed(3) : "-"}</td>
                    <td>{s?.FG3M?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FG3A?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FG3_PCT ? s.FG3_PCT.toFixed(3) : "-"}</td>
                    <td>{s?.FTM?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FTA?.toFixed(1) ?? "-"}</td>
                    <td>{s?.FT_PCT ? s.FT_PCT.toFixed(3) : "-"}</td>
                    <td>{s?.OREB?.toFixed(1) ?? "-"}</td>
                    <td>{s?.DREB?.toFixed(1) ?? "-"}</td>
                    <td>{s?.REB?.toFixed(1) ?? "-"}</td>
                    <td>{s?.AST?.toFixed(1) ?? "-"}</td>
                    <td>{s?.STL?.toFixed(1) ?? "-"}</td>
                    <td>{s?.BLK?.toFixed(1) ?? "-"}</td>
                    <td>{s?.TO?.toFixed(1) ?? "-"}</td>
                    <td>{s?.PF?.toFixed(1) ?? "-"}</td>
                    <td>{s?.PTS?.toFixed(1) ?? "-"}</td>
                    <td>{s?.PLUS_MINUS?.toFixed(1) ?? "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default PlayerDetail;
