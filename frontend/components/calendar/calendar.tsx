'use client';
import React, { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import styles from './calendar.module.css';

const Calendar: React.FC = () => {
  const [calendarOpen, setCalendarOpen] = useState<boolean>(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [currentMonth, setCurrentMonth] = useState<number>(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState<number>(new Date().getFullYear());

  const modalRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const toggleCalendar = (event: React.MouseEvent) => {
    setCalendarOpen(!calendarOpen);
    event.stopPropagation();
  };

  /* Closing modal by clicking outside of it*/
  const handleClickOutside = (event: MouseEvent) => {
    if (
      modalRef.current && !modalRef.current.contains(event.target as Node) &&
      buttonRef.current && !buttonRef.current.contains(event.target as Node)
    ) {
      setCalendarOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  /* Calendar setup */
  const getDaysInMonth = (month: number, year: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month: number, year: number) => {
    return new Date(year, month, 1).getDay();
  };

  const generateCalendar = () => {
    const daysInMonth = getDaysInMonth(currentMonth, currentYear);
    const firstDayOfMonth = getFirstDayOfMonth(currentMonth, currentYear);

    let daysArray = [];
    for (let i = 0; i < firstDayOfMonth; i++) {
      daysArray.push(null);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      daysArray.push(day);
    }
    return daysArray;
  };

  /* Setting selected date  */
  const handleDateSelect = (date: number) => {
    setSelectedDate(new Date(currentYear, currentMonth, date));
    setCalendarOpen(false);
  };

  /* Month change buttons */
  const changeMonth = (increment: number) => {
    const newMonth = currentMonth + increment;
    if (newMonth < 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else if (newMonth > 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(newMonth);
    }
  };

  /* Checking selected day for CSS */
  const isSelectedDay = (day: number) => {
    if (!selectedDate) return false;
    return (
      selectedDate.getDate() === day &&
      selectedDate.getMonth() === currentMonth &&
      selectedDate.getFullYear() === currentYear
    );
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      today.getDate() === day &&
      today.getMonth() === currentMonth &&
      today.getFullYear() === currentYear
    );
  };

  /* Calendar */
  const renderCalendar = () => {
    const daysArray = generateCalendar();
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    return (
      <div className={styles.calendar}>
        <div className={styles.month}>
          <button onClick={() => changeMonth(-1)}>&lt;</button>
          <span>{monthNames[currentMonth]} {currentYear}</span>
          <button onClick={() => changeMonth(1)}>&gt;</button>
        </div>
        <div className={styles.days}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
            <div key={index} className={styles.dayName}>
              {day}
            </div>
          ))}
          {daysArray.map((day, index) => (
            <div
              key={index}
              className={`${styles.day} ${day
                ? isSelectedDay(day)
                  ? `${styles.selected} ${isToday(day) ? styles.today : ''}`
                  : isToday(day)
                    ? styles.today
                    : ''
                : styles.empty
                }`}
              onClick={day ? () => handleDateSelect(day) : undefined}
            >
              {day}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className={styles.calendarLogo}>
        <button
          ref={buttonRef}
          className={styles.calendarButton}
          onClick={toggleCalendar}
          aria-label="Toggle Calendar"
        >
          <Image className={styles.image}
            src="/images/CalendarLogo.png"
            width={45}
            height={45}
            alt="logo"
          />
        </button>
      </div>

      {calendarOpen && (
        <div ref={modalRef} className={styles.calendarModal}>
          <div className={styles.dateSelector}>
            <h3>Select a Date</h3>
            {renderCalendar()}
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar;