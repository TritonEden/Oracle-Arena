"use client";

import React, { useEffect, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from "@tanstack/react-table";
import axios from "axios"; // For API calls
// import "./TableStyles.css"; // Ensure this file exists for styling

const NBAPlayersTable = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchNBAData = async () => {
      try {
        const response = await axios.get("/api/nba-players"); // Adjust endpoint as needed
        setData(response.data);
      } catch (error) {
        console.error("Error fetching NBA data:", error);
      }
    };

    fetchNBAData();
  }, []);

  const columns = [
    {
      accessorKey: "name",
      header: "Player Name",
    },
    {
      accessorKey: "points",
      header: "Points Per Game",
    },
    {
      accessorKey: "team",
      header: "Player Team",
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="table-container">
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default NBAPlayersTable;
