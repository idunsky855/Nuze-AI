import { useState, useEffect } from 'react'
import './App.css'
import Article from './components/Article'
import { fetchArticles } from './api'

function App() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadArticles = async () => {
      try {
        const data = await fetchArticles()
        setArticles(data)
      } catch (err) {
        setError('Failed to load articles')
      } finally {
        setLoading(false)
      }
    }

    loadArticles()
  }, [])

  if (loading) {
    return (
      <div className="loading-container">
        <p>Loading articles...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className="app-container">
      {articles.map((article, index) => (
        <Article key={article.id || index} article={article} />
      ))}
    </div>
  )
}

export default App
