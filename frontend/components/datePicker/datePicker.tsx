'use client';

import React, { useState, useEffect } from "react";
import { addDays, subDays } from "date-fns";
import styles from "./datePicker.module.css";

interface DateFilterProps {
  selectedDate: Date;
  setSelectedDate: (date: Date) => void;
}

const DateFilter: React.FC<DateFilterProps> = ({ selectedDate, setSelectedDate }) => {
  const today = new Date();
  const [isMobile, setIsMobile] = useState<boolean>(false);

  const getDateRange = () => {
    const startDate = subDays(selectedDate, isMobile ? 1 : 2); // Adjust based on mobile view
    const dates = [];

    // Add dates, ensuring the selected date is in the middle
    for (let i = 0; i < (isMobile ? 3 : 5); i++) {
      dates.push(addDays(startDate, i));
    }

    return dates;
  };

  const handleDateChange = (date: Date) => {
    setSelectedDate(date);
  };

  const isToday = (date: Date) => {
    return date.toDateString() === today.toDateString();
  };

  const getMonthName = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = { month: "long" };
    return new Intl.DateTimeFormat("en-US", options).format(date);
  };

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div className={styles.monthName}>
        {getMonthName(selectedDate)} {selectedDate.getFullYear()}
      </div>

      <div className="flex items-center">
        <button
          onClick={() => handleDateChange(subDays(selectedDate, 1))}
          disabled={selectedDate === subDays(today, 2)}
          className={styles.arrowButton}
        >
          &lt;
        </button>

        {getDateRange().map((date, index) => (
          <button
            key={index}
            onClick={() => handleDateChange(date)}
            className={`${styles.dateButton} ${date.toDateString() === selectedDate.toDateString()
                ? styles.selected
                : ""
              } ${isToday(date) ? styles.today : ""}`}
          >
            {date.getDate()}
          </button>
        ))}

        <button
          onClick={() => handleDateChange(addDays(selectedDate, 1))}
          disabled={selectedDate === addDays(today, 2)}
          className={styles.arrowButton}
        >
          &gt;
        </button>
      </div>
    </div>
  );
};

export default DateFilter;
