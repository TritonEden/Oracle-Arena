"use client";

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import styles from "./playerDetail.module.css";

interface PlayerGameStats {
  game_id: string;
  game_date: string;
  stats: { [key: string]: any };
}

interface AverageStats {
  season: string;
  stats: { [key: string]: number };
}

const PlayerDetail: React.FC = () => {
  const { player_id } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const season_year = searchParams.get("season") ?? "2024-25";
  const team_id = searchParams.get("team_id");

  const [stats, setStats] = useState<PlayerGameStats[]>([]);
  const [averageStats, setAverageStats] = useState<AverageStats[]>([]);
  const [playerName, setPlayerName] = useState<string>("");

  const [currentPage, setCurrentPage] = useState(1);
  const gamesPerPage = 10;

  useEffect(() => {
    fetch(`http://localhost:8000/api/players/`)
      .then((res) => res.json())
      .then((data) => {
        const foundPlayer = data.find((p: any) => p.player_id.toString() === player_id);
        if (foundPlayer) {
          setPlayerName(`${foundPlayer.first_name} ${foundPlayer.last_name}`);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch player name", err);
      });
  }, [player_id]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/api/player_stats_for_season/${player_id}/${season_year}/`
        );
        const data = await res.json();

        const uniqueGamesMap = new Map<string, any>();
        for (const entry of data) {
          if (entry.game_id.startsWith("2") && !uniqueGamesMap.has(entry.game_id)) {
            uniqueGamesMap.set(entry.game_id, entry);
          }
        }

        const uniqueGames = Array.from(uniqueGamesMap.values());

        const withDates: PlayerGameStats[] = await Promise.all(
          uniqueGames.map(async (entry: any) => {
            const dateRes = await fetch(`http://localhost:8000/api/game/${entry.game_id}/`);
            const dateData = await dateRes.json();
            const stats = JSON.parse(entry.player_game_stats);
        
            // Format the MIN field by splitting and trimming the extra decimals
            if (stats.MIN) {
              const [minutes, seconds] = stats.MIN.split(":");
              stats.MIN = `${parseInt(minutes)}:${seconds.padStart(2, "0")}`;
            }
        
            return {
              game_id: entry.game_id,
              game_date: dateData[0]?.game_date ?? "1970-01-01",
              stats: stats,
            };
          })
        );

        // Helper to check if all stats are zero, null, or empty string
        const isEmptyStats = (stats: { [key: string]: any }) => {
          return (
            !stats ||
            Object.values(stats).every(
              (val) => val === 0 || val === null || val === ""
            )
          );
        };

        const filteredStats = withDates.filter((entry) => !isEmptyStats(entry.stats));

        const sortedByDate = filteredStats.sort(
          (a, b) => new Date(b.game_date).getTime() - new Date(a.game_date).getTime()
        );

        setStats(sortedByDate);
      } catch (err) {
        console.error("Error fetching player season stats:", err);
      }
    };

    fetchStats();
  }, [player_id, season_year]);

  useEffect(() => {
    const years = Array.from({ length: 5 }, (_, i) => {
      const [start, end] = season_year.split("-");
      const prevStart = parseInt(start) - i;
      return `${prevStart}-${(parseInt(end) - i).toString().padStart(2, "0")}`;
    });

    Promise.all(
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
    ).then((results) => {
      const validResults = results.filter((item) => item !== null) as AverageStats[];
      setAverageStats(validResults);
    });
  }, [player_id, season_year]);

  const fullHeaders = (
    <tr>
      <th>Date</th>
      <th>MIN</th><th>FGM</th><th>FGA</th><th>FG%</th><th>FG3M</th><th>FG3A</th><th>FG3%</th>
      <th>FTM</th><th>FTA</th><th>FT%</th><th>OREB</th><th>DREB</th><th>REB</th>
      <th>AST</th><th>STL</th><th>BLK</th><th>TO</th><th>PF</th><th>PTS</th><th>+/-</th>
    </tr>
  );

  const avgHeaders = (
    <tr>
      <th>Season</th>
      <th>FGM</th><th>FGA</th><th>FG%</th><th>FG3M</th><th>FG3A</th><th>FG3%</th>
      <th>FTM</th><th>FTA</th><th>FT%</th><th>OREB</th><th>DREB</th><th>REB</th>
      <th>AST</th><th>STL</th><th>BLK</th><th>TO</th><th>PF</th><th>PTS</th><th>+/-</th>
    </tr>
  );

  const totalPages = Math.ceil(stats.length / gamesPerPage);
  const currentStats = stats.slice((currentPage - 1) * gamesPerPage, currentPage * gamesPerPage);

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

      {/* Recent Games Table */}
      <h2 style={{ color: "#cc9a36", marginBottom: "10px" }}>Recent Games</h2>
      <div className={styles.statsTable}>
        <table className={styles.statsTableContainer}>
          <thead>{fullHeaders}</thead>
          <tbody>
            {currentStats.map((stat, index) => (
              <tr key={index}>
                <td>{stat.game_date}</td>
                <td>
                  {stat.stats.MIN
                    ? stat.stats.MIN.split(":")[0] + ":" + stat.stats.MIN.split(":")[1].padStart(2, "0")
                    : "-"}
                </td>
                <td>{stat.stats.FGM}</td>
                <td>{stat.stats.FGA}</td>
                <td>{stat.stats.FG_PCT}</td>
                <td>{stat.stats.FG3M}</td>
                <td>{stat.stats.FG3A}</td>
                <td>{stat.stats.FG3_PCT}</td>
                <td>{stat.stats.FTM}</td>
                <td>{stat.stats.FTA}</td>
                <td>{stat.stats.FT_PCT}</td>
                <td>{stat.stats.OREB}</td>
                <td>{stat.stats.DREB}</td>
                <td>{stat.stats.REB}</td>
                <td>{stat.stats.AST}</td>
                <td>{stat.stats.STL}</td>
                <td>{stat.stats.BLK}</td>
                <td>{stat.stats.TO}</td>
                <td>{stat.stats.PF}</td>
                <td>{stat.stats.PTS}</td>
                <td>{stat.stats.PLUS_MINUS}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination Controls */}
        <div style={{ marginTop: "10px", textAlign: "center" }}>
          <button
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className={styles.paginationArrow}
          >
            &lt;
          </button>

          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => setCurrentPage(i + 1)}
              className={`${styles.paginationButton} ${
                currentPage === i + 1 ? styles.activePage : ""
              }`}
            >
              {i + 1}
            </button>
          ))}

          <button
            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className={styles.paginationArrow}
          >
            &gt;
          </button>
        </div>
      </div>

      {/* Season Averages Table */}
      <h2 style={{ color: "#cc9a36", marginTop: "40px", marginBottom: "10px" }}>Season Averages</h2>
      <div className={styles.statsTable}>
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
                  <td>{s?.FG_PCT?.toFixed(3) ?? "-"}</td>
                  <td>{s?.FG3M?.toFixed(1) ?? "-"}</td>
                  <td>{s?.FG3A?.toFixed(1) ?? "-"}</td>
                  <td>{s?.FG3_PCT?.toFixed(3) ?? "-"}</td>
                  <td>{s?.FTM?.toFixed(1) ?? "-"}</td>
                  <td>{s?.FTA?.toFixed(1) ?? "-"}</td>
                  <td>{s?.FT_PCT?.toFixed(3) ?? "-"}</td>
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
      </div>
    </div>
  );
};

export default PlayerDetail;
