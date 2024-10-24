// import Image from "next/image";
// import Link from "next/link";
import Navbar from '../../components/navbar/navbar';

export default function Home() {
  return (
    <main>
      <Navbar />
      <h1>HOME</h1>
      <h2>
        Coming Soon <span className="loadingDots"></span>
      </h2>
    </main>

  );
}
