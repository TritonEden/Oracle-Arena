'use client';

import React, { useState } from 'react';
import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar";
import SearchBar from "../../components/searchBar/searchBar";
import GameTable from "../../components/gameTable/gameTable";
import styles from './page.module.css';

export default function Home() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const formatToSQLDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const handleDateChange = (date: Date) => {
    setSelectedDate(date);

    const sqlDate = formatToSQLDate(date);
    console.log("SQL Date:", sqlDate); // Can eventually be removed, used for testing

    // Where API call will happen
  };

  return (
    <main>
      <div className={styles.filters}>
        <DatePicker selectedDate={selectedDate} setSelectedDate={handleDateChange} />
        <Calendar selectedDate={selectedDate} setSelectedDate={handleDateChange} />
        {/* <SearchBar /> */}
      </div>
      <div className={styles.gameTable}>
        <GameTable />
      </div>

    </main>

  );
}
