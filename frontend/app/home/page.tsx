'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar";
import GameTable from "../../components/gameTable/gameTable";
import styles from './page.module.css';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryDate = searchParams.get('date');

  const formatToSQLDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const parseDate = (dateStr: string): Date => {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  const [selectedDate, setSelectedDate] = useState<Date>(
    queryDate ? parseDate(queryDate) : new Date()
  );

  const handleDateChange = (date: Date) => {
    const formattedDate = formatToSQLDate(date);
    setSelectedDate(date);
    router.push(`?date=${formattedDate}`);
  };

  useEffect(() => {
    if (queryDate && formatToSQLDate(selectedDate) !== queryDate) {
      setSelectedDate(parseDate(queryDate));
    }
  }, [queryDate]);

  return (
    <main>
      <div className={styles.filters}>
        <DatePicker selectedDate={selectedDate} setSelectedDate={handleDateChange} />
        <Calendar selectedDate={selectedDate} setSelectedDate={handleDateChange} />
      </div>
      <div className={styles.gameTable}>
        <GameTable selectedDate={selectedDate} />
      </div>
    </main>
  );
}
