import React, { useState, useEffect } from 'react';
import styles from '../styles/SkillResources.module.css';

/**
 * Component to display and interact with skill resources
 * 
 * @param {Object} props Component props
 * @param {string} props.sessionId Current session ID
 * @param {string} props.skillName Name of the skill to show resources for
 * @param {string} props.proficiencyLevel Optional proficiency level to filter resources
 * @param {Function} props.onResourceSelect Callback when a resource is selected
 * @param {Function} props.onFeedback Callback when resource feedback is provided
 */
const SkillResources = ({
  sessionId,
  skillName,
  proficiencyLevel = null,
  onResourceSelect = () => {},
  onFeedback = () => {}
}) => {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('relevance');
  
  // Fetch resources when skill or proficiency changes
  useEffect(() => {
    if (!sessionId || !skillName) return;
    
    const fetchResources = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let url = `/api/interview/skill-resources?session_id=${sessionId}&skill_name=${encodeURIComponent(skillName)}`;
        if (proficiencyLevel) {
          url += `&proficiency_level=${encodeURIComponent(proficiencyLevel)}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch resources');
        }
        
        const data = await response.json();
        setResources(data);
      } catch (err) {
        console.error('Error fetching resources:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResources();
  }, [sessionId, skillName, proficiencyLevel]);
  
  // Sort and filter resources
  const displayedResources = React.useMemo(() => {
    let filtered = [...resources];
    
    // Apply type filter
    if (filter !== 'all') {
      filtered = filtered.filter(resource => resource.resource_type === filter);
    }
    
    // Apply sorting
    return filtered.sort((a, b) => {
      if (sortBy === 'relevance') {
        return b.relevance_score - a.relevance_score;
      } else if (sortBy === 'title') {
        return a.title.localeCompare(b.title);
      } else if (sortBy === 'type') {
        return a.resource_type.localeCompare(b.resource_type);
      }
      return 0;
    });
  }, [resources, filter, sortBy]);
  
  const handleResourceClick = (resource) => {
    // Track that this resource was clicked
    trackResourceClick(resource);
    // Call the provided callback
    onResourceSelect(resource);
    // Open in a new tab
    window.open(resource.url, '_blank', 'noopener,noreferrer');
  };
  
  const handleResourceFeedback = (resource, isHelpful) => {
    // Send feedback about the resource
    sendResourceFeedback(resource, isHelpful);
    // Call the provided callback
    onFeedback(resource, isHelpful);
  };
  
  const trackResourceClick = async (resource) => {
    try {
      await fetch('/api/interview/resource-tracking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          resource_id: resource.id,
          action: 'click',
          skill_name: skillName
        }),
      });
    } catch (err) {
      console.error('Error tracking resource click:', err);
    }
  };
  
  const sendResourceFeedback = async (resource, isHelpful) => {
    try {
      await fetch('/api/interview/resource-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          resource_id: resource.id,
          feedback: isHelpful ? 'helpful' : 'not_helpful',
          skill_name: skillName
        }),
      });
    } catch (err) {
      console.error('Error sending resource feedback:', err);
    }
  };
  
  const getResourceTypeIcon = (type) => {
    switch (type) {
      case 'article': return '📄';
      case 'course': return '🎓';
      case 'video': return '🎬';
      case 'tutorial': return '📝';
      case 'documentation': return '📚';
      case 'book': return '📕';
      case 'tool': return '🔧';
      case 'community': return '👥';
      default: return '🔗';
    }
  };
  
  // Get the unique resource types available to populate the filter dropdown
  const availableResourceTypes = React.useMemo(() => {
    return ['all', ...new Set(resources.map(r => r.resource_type))];
  }, [resources]);
  
  if (loading) {
    return <div className={styles.loading}>Loading resources...</div>;
  }
  
  if (error) {
    return <div className={styles.error}>Error: {error}</div>;
  }
  
  if (resources.length === 0) {
    return <div className={styles.empty}>No resources found for {skillName}.</div>;
  }
  
  return (
    <div className={styles.resourcesContainer}>
      <div className={styles.header}>
        <h3>Learning Resources for {skillName}</h3>
        <div className={styles.controls}>
          <div className={styles.filter}>
            <label htmlFor="resourceFilter">Filter: </label>
            <select 
              id="resourceFilter" 
              value={filter} 
              onChange={(e) => setFilter(e.target.value)}
            >
              {availableResourceTypes.map(type => (
                <option key={type} value={type}>
                  {type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.sort}>
            <label htmlFor="resourceSort">Sort by: </label>
            <select 
              id="resourceSort" 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="relevance">Relevance</option>
              <option value="title">Title</option>
              <option value="type">Type</option>
            </select>
          </div>
        </div>
      </div>
      
      <ul className={styles.resourceList}>
        {displayedResources.map((resource, index) => (
          <li key={index} className={styles.resourceItem}>
            <div className={styles.resourceHeader}>
              <span className={styles.resourceType}>
                {getResourceTypeIcon(resource.resource_type)} {resource.resource_type}
              </span>
              <span className={styles.relevanceScore}>
                {[...Array(Math.round(resource.relevance_score))].map((_, i) => (
                  <span key={i} className={styles.star}>★</span>
                ))}
              </span>
            </div>
            <h4 className={styles.resourceTitle} onClick={() => handleResourceClick(resource)}>
              {resource.title}
            </h4>
            <p className={styles.resourceDescription}>{resource.description}</p>
            <div className={styles.resourceActions}>
              <button 
                className={styles.actionButton}
                onClick={() => handleResourceClick(resource)}
              >
                Open Resource
              </button>
              <div className={styles.feedbackButtons}>
                <button 
                  className={styles.feedbackButton}
                  onClick={() => handleResourceFeedback(resource, true)}
                >
                  👍 Helpful
                </button>
                <button 
                  className={styles.feedbackButton}
                  onClick={() => handleResourceFeedback(resource, false)}
                >
                  👎 Not Helpful
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SkillResources; 