import React from 'react'
import Link from 'next/link'
import Navbar from "../../components/navbar/navbar"

const statistics = () => {
  return (
    <div>
      <Navbar />
      <h1 style={{ marginTop: '300px', textAlign: 'center'}}>STATISTICS</h1>
      <h2>
        Coming Soon <span className="loadingDots"></span>
      </h2>
    </div>
  )
}

export default statistics
