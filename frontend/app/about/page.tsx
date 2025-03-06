'use client';

import { useState } from 'react'
import styles from "./page.module.css";

const about = () => {
  const [isActive, setIsActive] = useState(false);

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageNav}>
        <button
          // className={`${styles.searchOverlay} ${!isActive ? styles.searchOverlayActive : ''}`}
          // onClick={showAbout}
          aria-label="Show About Sub-Page"
        >
          About the Team
        </button>
        <button
          // className={`${styles.searchOverlay} ${!isActive ? styles.searchOverlayActive : ''}`}
          // onClick={showAbout}
          aria-label="Show Model Explanation Sub-Page"
        >
          Model Explanation
        </button>
        <button
          // className={`${styles.searchOverlay} ${!isActive ? styles.searchOverlayActive : ''}`}
          // onClick={showAbout}
          aria-label="Show How to Use Data Visualization Sub-Page"
        >
          How to Use Data Visualization
        </button>
      </div>

      <div className="about">
        ...
      </div>
      <div className={styles.modelExplain}>
        ...
      </div>
      <div className={styles.useExplain}>
        ...
      </div>
    </div>
  )
}

export default about