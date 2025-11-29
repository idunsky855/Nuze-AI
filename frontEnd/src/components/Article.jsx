import React from 'react';

const Article = ({ article }) => {
    return (
        <div className="article-card" style={{ border: '1px solid #ccc', padding: '16px', margin: '16px 0', borderRadius: '8px' }}>
            <h2>{article.title}</h2>
            <p>{article.content}</p>
            {article.author && <small>By {article.author}</small>}
        </div>
    );
};

export default Article;
