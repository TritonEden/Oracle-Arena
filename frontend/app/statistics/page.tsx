"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { useReactTable, getCoreRowModel, flexRender } from "@tanstack/react-table";

interface Player {
  id: number;
  name: string;
  points_per_game: number;
  team_name: string;
}

const Statistics = () => {
  const [players, setPlayers] = useState<Player[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await axios.get("https://jsonplaceholder.typicode.com/users");
        setPlayers(data.map((player: any) => ({ id: player.id, name: player.name, points_per_game: Math.random() * 30, team_name: "Unknown" }))); // Mock points & team
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, []);

  const columns = [
    { accessorKey: "name", header: "Player Name" },
    { accessorKey: "points_per_game", header: "Points Per Game" },
    { accessorKey: "team_name", header: "Player Team" },
  ];

  const table = useReactTable({
    data: players,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <main>
      <div >
        <h1 className="text-center text-xl font-bold mb-4">Statistics</h1>
        <table className="border-collapse w-full border border-gray-300">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-gray-100">
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="border border-gray-300 p-2">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="border border-gray-300 p-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
};

export default Statistics;
