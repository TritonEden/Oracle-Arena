import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar";
import SearchBar from "../../components/searchBar/searchBar"
import styles from './page.module.css';

export default function Home() {
  return (
    <main>
      <div className={styles.filters}>
        <div className={styles.datePicker}>
          <DatePicker />
        </div>
        <div className={styles.calendar}>
          <Calendar />
        </div>
        <div className={styles.search}>
          <SearchBar />
        </div>
      </div>

      {/* 
        - Div table to display game schedule
        - This method was used for styling purposes
      */}
      <div className={styles.tableContainer}>
        <div className={styles.gamesTable}>
          <div className={styles.headerRow}>
            <div>Visiting Team</div>
            <div>at</div>
            <div>Home Team</div>
          </div>
          {/* Table Body */}
          <div className={styles.gameRow}>
            <div className={styles.tableCell}>Logo 1</div>
            <div className={styles.tableCell}>Team 1</div>
            <div className={styles.tableCell}>Start Time</div>
            <div className={styles.tableCell}>Team 2</div>
            <div className={styles.tableCell}>Logo 2</div>
          </div>
          <div className={styles.dataLabelRow}>
            <div className={styles.tableCell}>Winner (Prediction vs Actual)</div>
            <div className={styles.tableCell}>Total Score (Prediction vs Actual)</div>
          </div>
          <div className={styles.dataRow}>
            <div className={`${styles.tableCell} ${styles.actualData}`}>Pred. Winner</div>
            <div className={`${styles.tableCell} ${styles.predictData}`}>Act. Winner</div>
            <div className={`${styles.tableCell} ${styles.actualData}`}>Pred. Total</div>
            <div className={`${styles.tableCell} ${styles.predictData}`}>Act. Total</div>
          </div>
        </div>
      </div>

    </main>

  );
}
