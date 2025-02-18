"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel, flexRender } from "@tanstack/react-table";
import styles from "./Statistics.module.css"; // Import the CSS module

// Define Player interface
interface Player {
  id: number;
  name: string;
  points_per_game: number;
  team_name: string;
}

const Statistics = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [globalFilter, setGlobalFilter] = useState(""); // Global filter state
  const [columnFilters, setColumnFilters] = useState<{ [key: string]: string }>({}); // Column filters state

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await axios.get("https://jsonplaceholder.typicode.com/users");
        setPlayers(
          data.map((player: any) => ({
            id: player.id,
            name: player.name,
            points_per_game: Math.random() * 30, // Mocking PPG data
            team_name: player.address.street, // Mock name by using person's street
          }))
        );
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, []);

  const columns = [
    {
      accessorKey: "name",
      header: "Player Name",
      enableSorting: true,
      enableColumnFilter: true,
    },
    {
      accessorKey: "points_per_game",
      header: "Points Per Game",
      enableSorting: true,
      enableColumnFilter: true,
      cell: (info: any) => info.getValue().toFixed(2),
    },
    {
      accessorKey: "team_name",
      header: "Player Team",
      enableSorting: true,
      enableColumnFilter: true,
    },
  ];

  const table = useReactTable({
    data: players,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      globalFilter,
      columnFilters,
    },
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
  });

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Player Statistics</h1>

      <input
        type="text"
        placeholder="Search all columns..."
        value={globalFilter}
        onChange={(e) => setGlobalFilter(e.target.value)}
        className={styles.searchInput}
      />

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className={styles.tableHeaderRow}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className={styles.tableHeader}>
                    <div onClick={header.column.getToggleSortingHandler()} className={styles.sortableHeader}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === "asc" ? " 🔼" : header.column.getIsSorted() === "desc" ? " 🔽" : " ↕"}
                    </div>
                    <input
                      type="text"
                      placeholder="Filter..."
                      value={columnFilters[header.column.id] || ""}
                      onChange={(e) => setColumnFilters({ ...columnFilters, [header.column.id]: e.target.value })}
                      className={styles.filterInput}
                    />
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, index) => (
              <tr key={row.id} className={`${styles.tableRow} ${index % 2 === 0 ? styles.evenRow : styles.oddRow}`}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className={styles.tableCell}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Statistics;
