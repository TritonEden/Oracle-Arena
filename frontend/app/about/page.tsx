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
          Mission and Team
        </button>
        <button
          className={`${styles.navItem} ${activeSection === "model" ? styles.navItemActive : ''}`}
          onClick={() => handleSectionChange("model")}
          aria-label="Show Model Explanation Sub-Page"
        >
          Model Explanation
        </button>
      </div>

      {/* About Tab */}
      <div className={`${styles.about} ${styles.subPage}`} style={{ display: activeSection === "about" ? "block" : "none" }}>
        {/* Mission Statement */}
        <div className={styles.sectionLabel}>Mission Statement</div>
        <div className={styles.missionStatement}>
          Creating actionable insight for all levels of NBA fans.
        </div>

        {/* History */}
        <div className={styles.sectionLabel}>History</div>
        <div className={styles.history}>
          Oracle Arena was conceived in response to the fragmented landscape of NBA analytics tools, where fans, betters, and data 
          enthusiasts struggle with disjointed platforms that fail to provide a comprehensive, user friendly experience. With the rapid 
          growth of the sports betting industry and the increasing reliance on advanced analytics, we recognized the need for a solution 
          that integrates real time NBA data, predictive modeling, and data visualizations into a single, seamless platform. By 
          leveraging machine learning to generate transparent and insightful predictions, Oracle Arena aims to level the playing field, 
          empowering users with everything they need in one single location.
        </div>

        <div className={styles.sectionLabel}>Meet the Team</div>
        {/* Triton Eden */}
        <div className={styles.teamMemberA}>
          <div className={styles.imageContainerLeft}>
            <Image
              src="/images/tritonPicture.png"
              width={300}
              height={300}
              alt="Triton (J Smoove)"
                className={styles.image}
            />
          </div>
          <div className={styles.aboutMemberRight}>
            <p className={styles.name}>Triton Eden</p>
            <p className={styles.description}>Machine Learning Model</p>
            <p className={styles.text}>
              I became a basketball fan at 10 years old while watching the Miami Heat go on their run to win the finals in 2013.
              I have been a LeBron stan from day 1, and trust me, when I am in the gym I play just like him. As an NBA fan,
              I have always focused on players and love analyzing which stats best measure a player's impact on winning.
              I am constantly browsing Basketball Reference and I catch as many Lakers games as I can. I love using Oracle Arena
              as an NBA analysis tool. Finding out which statistics have most impact winning according to our models is incredibly
              exciting for me. Besides coming up with the idea for Oracle Arena, my primary work for this project has been developing
              the machine learning model used for our predictions, including training and testing. I have also worked on data extraction.
              <br></br>
              <br></br>
              <b>Fun Fact</b>: I have some of the best post moves in West Knoxville, and have been described as a "less athletic DeMar DeRozan".
            </p>
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
                into the betting process; all I need is pure statistical reasoning to convert picks into cold, hard cash. That is why I am so excited
                about Oracle Arena and the betting value it can provide. As someone who has not been too ingrained in the NBA statistics scene,
                this takes away a lot of the worry and boosts my confidence in my picks. I am excited for others to share in that feeling and to
                hopefully win some money! My responsibilities for this project largely include frontend work for the Home and About pages, and I
                am also responsible for design elements like layout, color scheme, logo creation, etc.
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
                className={styles.image}
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
                className={styles.image}
              />
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Nolan Coffey</p>
              <p className={styles.description}>Backend Development: DevOps</p>
              <p className={styles.text}>
                I have seen some NBA games, caught UT men's basketball, and played enough pickup to know there are two types of players: 
                those who call every foul and those who've studied Malice at the Palace like it is a game tape. I aspire to be somewhere 
                in between with aggressive box outs, minimal criminal charges. I am proud of what we have created with Oracle Arena, and 
                feel that we have made something for every type of basketball fan. I am excited to see how this project continues to evolve.
                I am responsible for working on our Backend Pipeline consisting of Nginx and Django, containerizing with Docker and deployment to Azure. 
                Through this project I've learned valuable DevOps skills and improved my ability to coordinate and communicate with a development 
                team.
                <br></br>
                <br></br>
                <b>Fun Fact</b>: The name on my driver's license says "Nolan", but on the court they call me the "Layup King".
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
                I am pretty sure that I have only touched a basketball 20 times in my entire lifespan. I discovered basketball in middle 
                school in PE class. It, sadly, did not discover me. This led to my teammates calling me "The Decoy" because nobody guards me. 
                Working on Oracle Arena has given me some valuable insight into the sport, especially individual player statistics. This is 
                because I created the Statistics page that hosts individual player performance data. Another role I took on is data collection 
                in order to get player data. My hope is that others like me can use the Statistics page to make themselves sound smarter about 
                the sport, just like I have been doing with the rest of the Oracle Arena team!
                <br></br>
                <br></br>
                <b>Fun Fact</b>: My favorite player is LeBron James. He is just like me if you think of coding as basketball.
              </p>
            </div>
            <div className={styles.imageContainerRight}>
              <Image
                src="/images/kienPicture.png"
                width={300}
                height={300}
                alt="Kien (Kong)"
                className={styles.image}
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
                alt="Peruski (Ram Slam)"
                className={styles.image}
              />
            </div>
            <div className={styles.aboutMemberRight}>
              <p className={styles.name}>Ryan Peruski</p>
              <p className={styles.description}>Backend Development: Data Management</p>
              <p className={styles.text}>
                I do not have much knowledge or experience with basketball, but I do know how to code. While I was excited
                to learn what I needed to about the NBA to successfully contribute to this project, what excited me the most
                about working on Oracle Arena was its size. This is not something that I could easily manage to do on my own.
                Utilizing my skills in database management as well as data collection, I am responsible for collecting the
                necessary NBA data, and creating a database for storage along with API endpoints for access.
                <br></br>
                <br></br>
                <b>Fun Fact</b>: My favorite player is Shaquille O'Neal, proud inventor of the Papa John's Shaq-a-Roni.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Prediction Model Explanation Tab*/}
      <div className={`${styles.modelInfo} ${styles.subPage}`} style={{ display: activeSection === "model" ? "block" : "none" }}>
        <div className={styles.sectionLabel}>Model Features</div>
        <div className={styles.subHeader}>Statistics Columns</div>
        <div className={styles.modelInfoText}>
          The stats columns used were field goals made (FGM), field goals attempted (FGA), three-point field goals made (FG3M), three-point 
          field goals attempted (FG3A), free throws made (FTM), free throws attempted (FTA), offensive rebounds (OREB), defensive rebounds 
          (DREB), assists (AST), steals (STL), blocks (BLK), turnovers (TO), points (PTS), estimated possessions (POSS), wins, and losses.
        </div>
        <div className={styles.modelInfoText}>
        The stats used as input to the models are from the 2018-19 NBA season to the current NBA season. Each of the stats in the stats columns
        are found for the home and away team per 100 possessions. Those stats are then averaged over the current season and over the past 5 games 
        for the team and their opponent’s stats.
        </div>
        <div className={styles.modelInfoText}>
        <Image className={styles.modelImage}
            src="/images/statsTree.png"
            width={2000}
            height={300}
            alt="Stats Tree"
          />
        </div>
        <div className={styles.modelInfoText}>
          The data is scaled with a Min-Max scaler to ensure equal contribution of features and then it is split into 80% training data and 20% 
          testing data. This split occurs without shuffling the data to prevent data leakage.
        </div>
        <div className={styles.modelInfoTableContainer}>
          {/* Win Prediction Table */}
          <div className={styles.modelInfoTable}>
            <div className={styles.dataTitle}>Win Prediction</div>
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>Regular Season</th>
                  <th>Playoffs</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td></td>
                  <td colSpan={2}>Deep Feedforward Nueral Network</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>Accuracy</td>
                  <td>0.66</td>
                  <td>0.67</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>F1 Score</td>
                  <td>0.71</td>
                  <td>0.73</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>Loss</td>
                  <td>0.62</td>
                  <td>0.66</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className={styles.modelInfoTable}>
            {/* Total Score Prediction Table */}
            <div className={styles.dataTitle}>Total Score Prediction</div>
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>Regular Season</th>
                  <th>Playoffs</th>
                </tr>
              </thead>
              <tbody>
              <tr>
                  <td></td>
                  <td>Gradient Boosting Regressor</td>
                  <td>Ridge Regression</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>RMSE</td>
                  <td>18.60</td>
                  <td>16.67</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>MSE</td>
                  <td>346.33</td>
                  <td>277.83</td>
                </tr>
                <tr>
                  <td className={styles.rowLabel}>R<sup>2</sup></td>
                  <td>0.11</td>
                  <td>0.08</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div className={styles.modelInfoText}>
          The playoff model has less data to train on, but because playoff games have less variance the playoff performance metrics are generally
          better than the regular season ones. NBA win prediction models commonly get accuracy between 60%-70% over much smaller test sets. 
        </div>
        <div className={styles.subHeader}>Win Prediction Models</div>
        <div className={styles.modelInfoText}>
          This neural network is a deep feedforward model built using Keras' Sequential API. It passes features through four hidden layers of 
          progressively smaller sizes: 256, 128, 64, and 32 neurons, respectively. Each hidden layer uses the ReLU activation function to introduce 
          non-linearity, which helps the network learn complex patterns in the data. To improve training stability and speed, each layer is followed 
          by batch normalization, which standardizes the inputs to the layer and reduces internal covariate shift. Additionally, dropout is applied 
          after each layer with increasing rates (from 30% up to 60%) to reduce overfitting by randomly deactivating a portion of the neurons during 
          training. The final layer is a dense layer with a single neuron and a sigmoid activation function, which outputs a probability between 0 and 
          1. 1 means the model predicts the home team to win and 0 means it predicted the away team. The model is compiled with the Nadam optimizer, 
          a variant of Adam that incorporates Nesterov momentum, and uses binary cross entropy as the loss function, which is standard for binary 
          classification problems. Accuracy is used as the performance metric during training and evaluation. The playoff model is the same as the 
          regular season but with slightly less dropout due to the lack of training data compared to the regular season model.
        </div>
        <div className={styles.modelInfoDataContainer}>
          <div>
            <div className={styles.dataTitle}>Regular Season Confusion Matrix</div>
            <Image className={styles.modelImage}
              src="/images/regSeasonConfusionMatrix.png"
              width={500}
              height={500}
              alt="Regular Season Confusion Matrix"
            />
          </div>
          <div>
            <div className={styles.dataTitle}>Playoffs Confusion Matrix</div>
            <Image className={styles.modelImage}
              src="/images/playoffConfusionMatrix.png"
              width={500}
              height={500}
              alt="Playoff Confusion Matrix"
            />
          </div>
        </div>
        <div className={styles.subHeader}>Total Score Prediction Models</div>
        <div className={styles.modelInfoText}>
          The regular season model uses XGBoost which is a decision tree based model that implements regularization techniques to improve model generalization 
          and prevent overfitting. The hyperparameters tuned version of this model performed best for the regular season. For the playoffs however the best 
          performing model was ridge regression. Playoff data is limited compared to the regular season data, so having lower model capacity likely made ridge 
          regression less prone to overfitting than XGBoost.
        </div>
        <div className={styles.modelInfoDataContainer}>
          <div>
            <div className={styles.dataTitle}>Regular Season Scatter Plot</div>
            <Image className={styles.modelImage}
              src="/images/regSeasonScatterPlot.png"
              width={500}
              height={500}
              alt="Regular Season Scatter Plot"
            />
          </div>
          <div>
            <div className={styles.dataTitle}>Playoff Scatter Plot</div>
            <Image className={styles.modelImage}
              src="/images/playoffScatterPlot.png"
              width={500}
              height={500}
              alt="Playoff Scatter Plot"
            />
          </div>
        </div>
        <div className={styles.modelInfoDataContainer}>
          <div>
            <div className={styles.dataTitle}>Regular Season Histogram</div>
            <Image className={styles.modelImage}
              src="/images/regSeasonHistogram.png"
              width={500}
              height={500}
              alt="Regular Season Histogram"
            />
          </div>
          <div>
            <div className={styles.dataTitle}>Playoff Histogram</div>
            <Image className={styles.modelImage}
              src="/images/playoffHistogram.png"
              width={500}
              height={500}
              alt="Playoff Histogram"
            />
          </div>
        </div>
        <div className={styles.disclaimer}>
          This model is not  accurate and has the potential to make incorrect predictions. We do not assume any 
          responsibility for any monetary loss or repercussions of decisions made based on its predictions.
        </div>
      </div>
    </div>
  );
};

export default About;
