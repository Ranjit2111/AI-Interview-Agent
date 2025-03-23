import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import SkillCard from '../components/SkillCard';
import styles from '../styles/Skills.module.css';

const SkillsPage = () => {
  const router = useRouter();
  const { session_id } = router.query;
  
  const [skills, setSkills] = useState([]);
  const [skillProfile, setSkillProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sortBy, setSortBy] = useState('proficiency');
  
  // Fetch skills and profile when session_id is available
  useEffect(() => {
    if (!session_id) return;
    
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch skills
        const skillsResponse = await fetch(`/api/interview/skills?session_id=${session_id}`);
        if (!skillsResponse.ok) {
          throw new Error('Failed to fetch skills');
        }
        const skillsData = await skillsResponse.json();
        setSkills(skillsData);
        
        // Fetch skill profile
        const profileResponse = await fetch(`/api/interview/skill-profile?session_id=${session_id}`);
        if (!profileResponse.ok) {
          throw new Error('Failed to fetch skill profile');
        }
        const profileData = await profileResponse.json();
        setSkillProfile(profileData);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [session_id]);
  
  // Resource tracking - when a user clicks on a resource
  const handleResourceSelect = (resource) => {
    console.log('Resource selected:', resource);
    // Analytics tracking could be implemented here if needed
  };
  
  // Filter and sort skills
  const filteredSkills = React.useMemo(() => {
    let filtered = [...skills];
    
    // Apply category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(skill => skill.category === categoryFilter);
    }
    
    // Apply sorting
    return filtered.sort((a, b) => {
      if (sortBy === 'proficiency') {
        return b.proficiency - a.proficiency;
      } else if (sortBy === 'name') {
        return a.skill_name.localeCompare(b.skill_name);
      } else if (sortBy === 'category') {
        return a.category.localeCompare(b.category);
      }
      return 0;
    });
  }, [skills, categoryFilter, sortBy]);
  
  // Get unique categories for filter dropdown
  const categories = React.useMemo(() => {
    return ['all', ...new Set(skills.map(skill => skill.category))];
  }, [skills]);
  
  if (loading) {
    return (
      <div className={styles.container}>
        <Head>
          <title>Skills Assessment - AI Interviewer</title>
        </Head>
        <div className={styles.loading}>Loading skills assessment...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={styles.container}>
        <Head>
          <title>Error - AI Interviewer</title>
        </Head>
        <div className={styles.error}>Error: {error}</div>
      </div>
    );
  }
  
  return (
    <div className={styles.container}>
      <Head>
        <title>Skills Assessment - AI Interviewer</title>
      </Head>
      
      <header className={styles.header}>
        <h1 className={styles.title}>Skills Assessment</h1>
        <button 
          className={styles.backButton}
          onClick={() => router.push(`/interview?session_id=${session_id}`)}
        >
          Back to Interview
        </button>
      </header>
      
      {skillProfile && (
        <div className={styles.profileOverview}>
          <div className={styles.jobMatch}>
            <h2>Job Match</h2>
            <div className={styles.matchPercentage}>
              <span className={styles.percentValue}>{skillProfile.overall_match}%</span>
              <div className={styles.percentBar}>
                <div 
                  className={styles.percentFill}
                  style={{ width: `${skillProfile.overall_match}%` }}
                />
              </div>
            </div>
          </div>
          
          <div className={styles.strengthsWeaknesses}>
            <div className={styles.strengths}>
              <h3>Strengths</h3>
              <ul className={styles.itemList}>
                {skillProfile.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </div>
            
            <div className={styles.weaknesses}>
              <h3>Areas for Improvement</h3>
              <ul className={styles.itemList}>
                {skillProfile.improvement_areas.map((area, index) => (
                  <li key={index}>{area}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
      
      <div className={styles.skillsControls}>
        <div className={styles.totalSkills}>
          <span className={styles.skillCount}>{filteredSkills.length}</span> skills assessed
        </div>
        
        <div className={styles.filters}>
          <div className={styles.filter}>
            <label htmlFor="categoryFilter">Category: </label>
            <select 
              id="categoryFilter" 
              value={categoryFilter} 
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>
          
          <div className={styles.filter}>
            <label htmlFor="sortBy">Sort by: </label>
            <select 
              id="sortBy" 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="proficiency">Proficiency (High to Low)</option>
              <option value="name">Skill Name</option>
              <option value="category">Category</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className={styles.skillsList}>
        {filteredSkills.length > 0 ? (
          filteredSkills.map((skill, index) => (
            <SkillCard 
              key={index}
              skill={skill}
              sessionId={session_id}
              onResourceSelect={handleResourceSelect}
            />
          ))
        ) : (
          <div className={styles.noSkills}>
            No skills match the selected filter.
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillsPage; 