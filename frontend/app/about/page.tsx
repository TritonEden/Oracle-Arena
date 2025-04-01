'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import styles from "./page.module.css";

const About = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultSection = searchParams.get("section") || "about";
  const [activeSection, setActiveSection] = useState<string>(defaultSection);

  useEffect(() => {
    setActiveSection(defaultSection);
  }, [defaultSection]);

  const handleSectionChange = (section: string) => {
    setActiveSection(section);
    router.push(`?section=${section}`, { scroll: false });
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageNav}>
        <button
          className={`${styles.navItem} ${activeSection === "about" ? styles.navItemActive : ''}`}
          onClick={() => handleSectionChange("about")}
          aria-label="Show About Sub-Page"
        >
          About the Team
        </button>
        <button
          className={`${styles.navItem} ${activeSection === "model" ? styles.navItemActive : ''}`}
          onClick={() => handleSectionChange("model")}
          aria-label="Show Model Explanation Sub-Page"
        >
          Model Explanation
        </button>
        <button
          className={`${styles.navItem} ${activeSection === "use" ? styles.navItemActive : ''}`}
          onClick={() => handleSectionChange("use")}
          aria-label="Show How to Use Data Visualization Sub-Page"
        >
          How to Use Data Visualization
        </button>
      </div>

      {/* About Tab */}
      <div className={`${styles.about} ${styles.subPage}`} style={{ display: activeSection === "about" ? "block" : "none" }}>
        {/* Triton Eden */}
        <div>
          <div className={styles.teamMemberA}>
            <div className={styles.imageContainerLeft}>
              image
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Triton Eden</p>
              <p className={styles.description}>Machine Learning Model</p>
            </div>
          </div>
          <div className={styles.text}>
            text
          </div>
        </div>
        {/* William Duff */}
        <div>
          <div className={styles.teamMemberB}>
            <div className={styles.aboutMemberLeft}>
              <p className={styles.name}>William Duff</p>
              <p className={styles.description}>Frontend Development: Home / About</p>
            </div>
            <div className={styles.imageContainerRight}>
              image
            </div>
          </div>
          <div className={styles.text}>
            text
          </div>
        </div>
        {/* Nolan Coffey */}
        <div>
          <div className={styles.teamMemberA}>
            <div className={styles.imageContainerLeft}>
              image
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Nolan Coffey</p>
              <p className={styles.description}>Backend Development</p>
            </div>
          </div>
          <div className={styles.text}>
            text
          </div>
        </div>
        {/* Kien Nguyen */}
        <div>
          <div className={styles.teamMemberB}>
            <div className={styles.aboutMemberLeft}>
              <p className={styles.name}>Kien Nguyen</p>
              <p className={styles.description}>Frontend Development: Statistics</p>
            </div>
            <div className={styles.imageContainerRight}>
              image
            </div>
          </div>
          <div className={styles.text}>
            text
          </div>
        </div>
        {/* Ryan Peruski */}
        <div>
          <div className={styles.teamMemberA}>
            <div className={styles.imageContainerLeft}>
              image
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Ryan Peruski</p>
              <p className={styles.description}>Backend Development</p>
            </div>
          </div>
          <div className={styles.text}>
            text
          </div>
        </div>
      </div>

      {/* Prediction Model Explanation Tab*/}
      <div className={`${styles.modelExplain} ${styles.subPage}`} style={{ display: activeSection === "model" ? "block" : "none" }}>
        This is the section that explains how the prediction model works.
      </div>

      {/* Data Visualizations Tab */}
      <div className={`${styles.useExplain} ${styles.subPage}`} style={{ display: activeSection === "use" ? "block" : "none" }}>
        This is the section that explains how to use the data visualizations.
      </div>
    </div>
  );
};

export default About;
