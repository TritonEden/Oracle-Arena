import React from 'react'
// import Link from 'next/link'
import Navbar from "../../components/navbar/navbar"

// Information about the player is stored in this interface
interface Player {
  id: number;
  name: string;
  address: {
    street: string;
  };
}

const statistics = async () => {
  // fetch statistics data from a json placeholder (for now) and display the names of the players
  // cache: 'no-store' allows the page to be server rendered on command
  const res = await fetch('https://jsonplaceholder.typicode.com/users', {cache: 'no-store'})

  // When we have backend up, we can revalidate this information and refresh our cache
  // const res = await fetch('https://jsonplaceholder.typicode.com/users', {next: {revalidate: 1000}})
  const players: Player[] = await res.json()

  return (
    <div>
      <Navbar />
      <h1 style={{ marginTop: '300px', textAlign: 'center'}}>STATISTICS</h1>
      <br></br>
      <p>{new Date().toLocaleDateString()}</p>
      <p>{new Date().toLocaleTimeString()}</p>
      <h2 style={{ listStyleType: 'none', paddingLeft: '75px', textAlign: 'left' }}>Players</h2>
      <ul style={{ listStyleType: 'disc', paddingLeft: '100px', textAlign: 'left' }}>
        {players.map(player => 
          <li key={player.id}> 
            {player.name} - {player.address.street}
          </li>
        )}
      </ul>
      {/* <h2>
        Coming Soon <span className="loadingDots"></span>
      </h2> */}
    </div>
  )
}

export default statistics
