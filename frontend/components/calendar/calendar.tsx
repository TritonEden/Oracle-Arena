'use client'
import React, { useState } from 'react';
import Image from 'next/image';
import styles from './calendar.module.css';

const Calendar: React.FC = () => {
  const [calendarOpen, setCalendarOpen] = useState<boolean>(false);

  const toggleCalendar = () => {
    setCalendarOpen(!calendarOpen);
  };

  return (
    <div className={styles.calendarLogo}>
      <Image
        src="/images/CalendarLogo.png"
        width={48}
        height={55}
        alt="logo"
      />
    </div>
  );
};

export default Calendar;