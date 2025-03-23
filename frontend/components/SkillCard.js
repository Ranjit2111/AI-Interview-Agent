import React, { useState } from 'react';
import SkillResources from './SkillResources';
import styles from '../styles/SkillCard.module.css';

/**
 * Component for displaying a skill assessment with resources
 * 
 * @param {Object} props Component props
 * @param {Object} props.skill The skill assessment data
 * @param {string} props.sessionId Current session ID
 * @param {Function} props.onResourceSelect Callback when a resource is selected
 */
const SkillCard = ({
  skill,
  sessionId,
  onResourceSelect = () => {}
}) => {
  const [showResources, setShowResources] = useState(false);
  const [resourceFeedback, setResourceFeedback] = useState({});
  
  // Map proficiency level to color and label
  const getProficiencyInfo = (level) => {
    const levels = {
      1: { color: '#e74c3c', label: 'Beginner' },
      2: { color: '#e67e22', label: 'Basic' },
      3: { color: '#f1c40f', label: 'Intermediate' },
      4: { color: '#2ecc71', label: 'Advanced' },
      5: { color: '#27ae60', label: 'Expert' }
    };
    
    return levels[level] || { color: '#95a5a6', label: 'Unknown' };
  };
  
  const proficiencyInfo = getProficiencyInfo(skill.proficiency);
  
  // Generate proficiency bar segments
  const renderProficiencyBar = () => {
    const bars = [];
    for (let i = 1; i <= 5; i++) {
      bars.push(
        <div 
          key={i}
          className={styles.proficiencySegment}
          style={{
            backgroundColor: i <= skill.proficiency ? proficiencyInfo.color : '#3a3a3a'
          }}
        />
      );
    }
    return bars;
  };
  
  // Handle resource feedback
  const handleResourceFeedback = (resource, isHelpful) => {
    setResourceFeedback({
      ...resourceFeedback,
      [resource.id]: isHelpful
    });
  };
  
  return (
    <div className={styles.skillCard}>
      <div className={styles.skillHeader}>
        <h3 className={styles.skillName}>{skill.skill_name}</h3>
        <div className={styles.skillCategory}>{skill.category}</div>
      </div>
      
      <div className={styles.proficiency}>
        <div className={styles.proficiencyLabel}>
          Proficiency: <span style={{ color: proficiencyInfo.color }}>{proficiencyInfo.label}</span>
        </div>
        <div className={styles.proficiencyBarContainer}>
          {renderProficiencyBar()}
        </div>
      </div>
      
      <div className={styles.skillFeedback}>
        <p>{skill.feedback}</p>
      </div>
      
      <div className={styles.resourcesSection}>
        <button 
          className={styles.resourcesToggle}
          onClick={() => setShowResources(!showResources)}
        >
          {showResources ? 'Hide Resources' : 'Show Learning Resources'} ({skill.resources?.length || 0})
        </button>
        
        {showResources && (
          <div className={styles.resourcesContainer}>
            <SkillResources 
              sessionId={sessionId}
              skillName={skill.skill_name}
              proficiencyLevel={proficiencyInfo.label.toLowerCase()}
              onResourceSelect={onResourceSelect}
              onFeedback={handleResourceFeedback}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillCard; 