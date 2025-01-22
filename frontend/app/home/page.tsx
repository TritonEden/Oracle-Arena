// import Image from "next/image";
// import Link from "next/link";
import DatePicker from "../../components/datePicker/datePicker";
import Calendar from "../../components/calendar/calendar"

export default function Home() {
  return (
    <main>
      <div className="nav">
      </div>
      <div className="filters">
        <div className="datePicker">
          <DatePicker />
        </div>
        <div className="calendar">
          <Calendar />
        </div>
        <div className="search">
          <p>Search</p>
        </div>
      </div>
    </main>

  );
}
