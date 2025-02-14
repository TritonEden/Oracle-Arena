'use client';

import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import styles from './searchBar.module.css';

const SearchBar: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const searchBarRef = useRef<HTMLDivElement>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
  };

  const ShowSearch = (event: React.MouseEvent) => {
    setIsActive(true);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    event.stopPropagation();
  };

  /* 
  *  Event handlers for 'esc' being pressed and clicking outside the text box
  *    For 'esc' - if the text box has characters, do not close the text box but lose focus
  *    For clicking outside - ^^
  */


  // NEED 'esc' BEING PRESSED TO MAKE ROTATION ANIMATION TO HAPPEN IN REVERSE
  // REMOVE CONSOLE LOGS

  // useEffect(() => {
  //   const handleKeyDown = (event: KeyboardEvent) => {
  //     if (event.key === 'Escape') {
  //       console.log("Escape pressed")
  //       setIsActive(false);

  //       const toggleButton = document.querySelector(`.${styles.toggleSearch}`);
  //       if (toggleButton) {
  //         // Check if the class is being applied correctly
  //         console.log("Adding reverse class");
  //         toggleButton.classList.add(styles.reverse);
  //       }
  //     }
  //   };

  //   document.addEventListener('keydown', handleKeyDown);

  //   return () => {
  //     document.removeEventListener('keydown', handleKeyDown);
  //   };
  // }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchBarRef.current &&
        !searchBarRef.current.contains(event.target as Node)
      ) {
        setIsActive(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  return (
    <div className={styles.searchBar}>
      {isActive && (
        <input
          ref={inputRef}
          type="text"
          placeholder="Search"
          value={text}
          onChange={handleInputChange}
          className={styles.textBox}
        />
      )}

      {isActive ? (
        <button
          className={styles.toggleSearch}
          // onClick={Search}
          aria-label="Commense Search"
        >
          <Image
            className={styles.image}
            src="/images/searchLogo.png"
            width={30}
            height={30}
            alt="searchLogo"
          />
        </button>
      ) : (
        <button
          className={styles.searchOverlay}
          onClick={ShowSearch}
          aria-label="Show Search Bar"
        >
          <Image
            className={styles.imageOverlay}
            src="/images/searchLogo.png"
            width={30}
            height={30}
            alt="searchLogoOverlay"
          />
        </button>
      )}
    </div>
  );
};

export default SearchBar;
