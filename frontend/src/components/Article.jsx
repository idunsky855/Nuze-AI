import React, { useState } from 'react';
import { recordInteraction } from '../api';

const Article = ({ article }) => {
    const [interaction, setInteraction] = useState(null);

    const handleInteraction = (type) => {
        setInteraction(type);
        recordInteraction(article.id, type);
    };

    return (
        <div className={`article-card ${interaction}`}>
            <div className="article-content">
                <h2 className="article-title">{article.title}</h2>
                <p className="article-body">{article.content}</p>
                <div className="article-meta">
                    {article.author && <span>By {article.author}</span>}
                    {article.published_at && <span> • {new Date(article.published_at).toLocaleDateString()}</span>}
                </div>
            </div>
            <div className="interaction-buttons">
                <button className="like-button" onClick={() => handleInteraction('like')} aria-label="Like">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 21.35L10.55 20.03C5.4 15.36 2 12.28 2 8.5C2 5.42 4.42 3 7.5 3C9.24 3 10.91 3.81 12 5.09C13.09 3.81 14.76 3 16.5 3C19.58 3 22 5.42 22 8.5C22 12.28 18.6 15.36 13.45 20.04L12 21.35Z" />
                    </svg>
                </button>
                <button className="dislike-button" onClick={() => handleInteraction('dislike')} aria-label="Dislike">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16.5 3C14.76 3 13.09 3.81 12 5.09C10.91 3.81 9.24 3 7.5 3C4.42 3 2 5.42 2 8.5C2 12.28 5.4 15.36 10.55 20.03L12 21.35L13.45 20.03C14.88 18.73 16.16 17.38 17.26 16.03L15.3 14.07C14.47 15.15 13.43 16.22 12.23 17.3L12 17.51L11.77 17.3C7.27 13.21 4.5 10.65 4.5 8.5C4.5 6.8 5.79 5.5 7.5 5.5C8.83 5.5 10.12 6.36 10.58 7.55H13.43C13.88 6.36 15.17 5.5 16.5 5.5C18.21 5.5 19.5 6.8 19.5 8.5C19.5 9.22 19.23 9.9 18.78 10.54L20.64 12.4C21.5 11.28 22 10 22 8.5C22 5.42 19.58 3 16.5 3ZM21.5 21.5L2.5 2.5L3.91 1.09L22.91 20.09L21.5 21.5Z" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default Article;
