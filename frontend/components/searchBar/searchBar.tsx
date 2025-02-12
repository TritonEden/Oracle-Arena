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

  const toggleSearchBar = (event: React.MouseEvent) => {
    setIsActive(true);
    inputRef.current?.focus();
    event.stopPropagation();
  };

  /* 
  *  Event handlers for 'esc' being pressed and clicking outside the text box
  *    For 'esc' - if the text box has characters, do not close the text box but lose focus
  *    For clicking outside - ^^
  */

  // useEffect(() => {
  //   const handleKeyDown = (event: KeyboardEvent) => {
  //     if (event.key === 'Escape') {
  //       setIsActive(false);
  //     }
  //   };
  //   document.addEventListener('keydown', handleKeyDown);

  //   return () => {
  //     document.removeEventListener('keydown', handleKeyDown);
  //   };
  // }, []);

  // useEffect(() => {
  //   const handleClickOutside = (event: MouseEvent) => {
  //     if (
  //       searchBarRef.current &&
  //       !searchBarRef.current.contains(event.target as Node)
  //     ) {
  //       setIsActive(false);
  //     }
  //   };

  //   document.addEventListener('click', handleClickOutside);
  //   return () => {
  //     document.removeEventListener('click', handleClickOutside);
  //   };
  // }, []);

  return (
    <div className={styles.searchBar} ref={searchBarRef}>
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

      <button
        className={styles.toggleSearch}
        onClick={toggleSearchBar}
        aria-label="Toggle Search"
      >
        <Image
          className={styles.image}
          src="/images/searchLogo.png"
          width={30}
          height={30}
          alt="searchLogo"
        />
      </button>
    </div>
  );
};

export default SearchBar;
