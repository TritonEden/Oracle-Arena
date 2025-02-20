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

  const showSearch = (event: React.MouseEvent) => {
    setIsActive(true);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    event.stopPropagation();
  };

  const clearInput = () => {
    setText('');
    inputRef.current?.focus();
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsActive(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchBarRef.current &&
        !searchBarRef.current.contains(event.target as Node)
      ) {
        if (text.trim() === '') {
          setIsActive(false);
        }
      }
    };

    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [text]);


  return (
    <div className={styles.searchBar} ref={searchBarRef}>
      {isActive && (
        <div className={styles.textBoxWrapper}>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search"
            value={text}
            onChange={handleInputChange}
            className={styles.textBox}
          />
          {text && isActive && (
            <button
              className={styles.clearButton}
              onClick={clearInput}
              aria-label="Clear input"
            >
              &times; {/* The 'X' button */}
            </button>
          )}
      </div>
      )}

      {isActive ? (
        <button
          className={styles.searchButton}
          aria-label="Commence Search"
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
          className={`${styles.searchOverlay} ${!isActive ? styles.searchOverlayActive : ''}`}
          onClick={showSearch}
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
