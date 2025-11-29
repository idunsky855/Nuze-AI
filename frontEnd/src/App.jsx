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
        // For demo purposes if API fails, we could load mock data here if desired, 
        // but for now we show error.
      } finally {
        setLoading(false)
      }
    }

    loadArticles()
  }, [])

  return (
    <div className="App">
      <h1>Nuze Articles</h1>
      {loading && <p>Loading articles...</p>}
      {error && <p className="error">{error}</p>}
      <div className="article-list">
        {articles.map((article, index) => (
          <Article key={article.id || index} article={article} />
        ))}
      </div>
    </div>
  )
}

export default App
