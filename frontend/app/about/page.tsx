import React from 'react'
import Navbar from '../../components/navbar/navbar'

const about = () => {
  return (
    <div>
      <Navbar />
        <h1 style={{ marginTop: '300px', textAlign: 'center' }}>ABOUT</h1>
        <h2>
          Coming Soon <span className="loadingDots"></span>
        </h2>
    </div>
  )
}

export default about