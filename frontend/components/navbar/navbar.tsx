'use client';
import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import styles from './navbar.module.css';

const Navbar: React.FC = () => {
    const [menuOpen, setMenuOpen] = useState<boolean>(false);

    const toggleMenu = () => {
        setMenuOpen(!menuOpen);
    };

    return (
        <nav className={styles.navbar}>
            <div className={styles.navContainer}>
                <Link href="home">
                    <Image
                        src="/images/LogoWithText.png"
                        width={300}
                        height={100}
                        alt="logo"
                    />
                </Link>

                {/* Hamburger Menu Icon */}
                <button className={styles.menuButton} onClick={toggleMenu} aria-label="Toggle menu">
                    ☰
                </button>

                {/* Navigation Links */}
                <ul className={`${styles.navLinks} ${menuOpen ? styles.active : ''}`}>
                    <li>
                        <Link href="home">Home</Link>
                    </li>
                    <li>
                        <Link href="statistics">Stats</Link>
                    </li>
                    <li>
                        <Link href="about">About</Link>
                    </li>
                </ul>
            </div>
        </nav>
    );
};

export default Navbar;