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
                I became a basketball fan at 10 years old while watching the Miami Heat go on their run to win the finals in 2013.
                I have been a LeBron stan from day 1, and trust me, when I am in the gym I play just like him. As an NBA fan,
                I have always focused on players and love analyzing which stats best measure a player's impact on winning.
                I'm constantly browsing Basketball Reference and I catch as many Lakers games as I can. I love using Oracle Arena
                as an NBA analysis tool. Finding out which statistics have most impact winning according to our models is incredibly
                exciting for me. Besides coming up with the idea for Oracle Arena, my primary work for this project has been developing
                the machine learning model used for our predictions, including training and testing. I have also worked on data extraction.
                <br></br>
                <br></br>
                <b>Fun Fact</b>: I have some of the best post moves in West Knoxville, and have been described as a "less athletic DeMar DeRozan".
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
                I grew up watching college basketball and as I grew older started gaining more interest in the NBA. My interest grew tenfold when
                I found out that I could win oodles of money by betting on game outcomes. No need for a favorite team or player to incorporate biases
                into the betting process; all I need is pure statistical reasoning to convert into cold, hard cash. That is why I am so excited
                about Oracle Arena and the betting value it can provide. As someone who has not been too ingrained in the NBA statistics scene,
                this takes away a lot of the worry and boosts my confidence in my picks. I am excited for others to shar in that feeling and to
                hopefully win some money! My responsibilities for this project largely included frontend work for the Home and About pages, and I
                was also responsible for design elements like layout, color scheme, logo creation, etc.
                <br></br>
                <br></br>
                <b>Fun Fact</b>: No one can out rebound me. No one.
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
                I do not have much knowledge or experience with basketball, but I do know how to code. While I was excited
                to learn what I needed to about the NBA to successfully contribute to this project, what excited me the most
                about working on Oracle Arena was its size. This is not something that I could easily manage to do on my own.
                Utilizing my skills in database management as well as data collection, I was responsible for collecting the
                necessary NBA data, and created a database for storage along with API endpoints for access.
                <br></br>
                <br></br>
                <b>Fun Fact</b>: My favorite player is Shaquille O'Neal, proud inventor of the Papa John's Shaq-a-Roni.
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
