import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar";
import SearchBar from "../../components/searchBar/searchBar";
import GameTable from "../../components/gameTable/gameTable";
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
      <div className={styles.gameTable}>
        <GameTable />
      </div>

    </main>

  );
}
