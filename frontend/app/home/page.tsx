// import Image from "next/image";
// import Link from "next/link";
import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar"
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
          <p>Search</p>
        </div>
      </div>

      <div className={styles.tableContainer}>
        <table className={styles.gamesTable}>
          <thead>
            <tr>
              <th>Logo A</th>
              <th>Name A</th>
              <th>VS.</th>
              <th>Name B</th>
              <th>Logo B</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Welp</td>
            </tr>
          </tbody>
        </table>
      </div>

    </main>

  );
}
