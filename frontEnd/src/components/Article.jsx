import React from 'react';

const Article = ({ article }) => {
    return (
        <div className="article-card">
            <div className="article-content">
                <h2 className="article-title">{article.title}</h2>
                <p className="article-body">{article.content}</p>
                <div className="article-meta">
                    {article.author && <span>By {article.author}</span>}
                    {article.published_at && <span> • {new Date(article.published_at).toLocaleDateString()}</span>}
                </div>
            </div>
        </div>
    );
};

export default Article;
