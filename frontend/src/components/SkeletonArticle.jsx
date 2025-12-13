import React from 'react';
import '../App.css';

const SkeletonArticle = () => {
  return (
    <div className="article-card skeleton-card">
      <div className="article-content" style={{ width: '100%' }}>
        <div className="skeleton skeleton-title"></div>
        <div className="skeleton skeleton-image"></div>
        <div className="skeleton skeleton-text"></div>
        <div className="skeleton skeleton-text short"></div>
        <div className="skeleton skeleton-meta"></div>
      </div>
    </div>
  );
};

export default SkeletonArticle;
