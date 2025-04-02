'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import styles from './page.module.css';

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
              <Image
                src="/images/tritonPicture.png"
                width={300}
                height={300}
                alt="Triton (J Smoove)"
              />
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Triton Eden</p>
              <p className={styles.description}>Machine Learning Model</p>
              <p className={styles.text}>
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
              </p>
            </div>
          </div>
        </div>
        {/* William Duff */}
        <div>
          <div className={styles.teamMemberB}>
            <div className={styles.aboutMemberLeft}>
              <p className={styles.name}>William Duff</p>
              <p className={styles.description}>Frontend Development: Home / About</p>
              <p className={styles.text}>
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
              </p>
            </div>
            <div className={styles.imageContainerRight}>
              <Image
                src="/images/willPicture.png"
                width={300}
                height={300}
                alt="Will (Shaq-a-roni)"
              />
            </div>
          </div>
        </div>
        {/* Nolan Coffey */}
        <div>
          <div className={styles.teamMemberA}>
            <div className={styles.imageContainerLeft}>
              <Image
                src="/images/nolanPicture.png"
                width={300}
                height={300}
                alt="Nolan (Swaggy C)"
              />
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Nolan Coffey</p>
              <p className={styles.description}>Backend Development: DevOps</p>
              <p className={styles.text}>
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
              </p>
            </div>
          </div>
        </div>
        {/* Kien Nguyen */}
        <div>
          <div className={styles.teamMemberB}>
            <div className={styles.aboutMemberLeft}>
              <p className={styles.name}>Kien Nguyen</p>
              <p className={styles.description}>Frontend Development: Statistics</p>
              <p className={styles.text}>
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
              </p>
            </div>
            <div className={styles.imageContainerRight}>
              <Image
                src="/images/kienPicture.png"
                width={300}
                height={300}
                alt="Kien (Kong)"
              />
            </div>
          </div>
        </div>
        {/* Ryan Peruski */}
        <div>
          <div className={styles.teamMemberA}>
            <div className={styles.imageContainerLeft}>
              <Image
                src="/images/peruskiPicture.png"
                width={300}
                height={300}
                alt="Persuki (Ram Slam)"
              />
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Ryan Peruski</p>
              <p className={styles.description}>Backend Development: Data Management</p>
              <p className={styles.text}>
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
                Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.
              </p>
            </div>
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
