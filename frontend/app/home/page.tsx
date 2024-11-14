// import Image from "next/image";
// import Link from "next/link";
import Navbar from '../../components/navbar/navbar';
import MyDayPicker from "../../components/datePicker/datePicker";

export default function Home() {
  return (
    <main>
      <div className="nav">
        <Navbar />
      </div>
      <div className="filters">
        <div className="datePicker">
          <MyDayPicker />
        </div>
        
      </div>
    </main>

  );
}
