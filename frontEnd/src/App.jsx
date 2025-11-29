import { useState, useEffect } from 'react'
import './App.css'
import Article from './components/Article'
import Login from './components/Login'
import Signup from './components/Signup'
import Preferences from './components/Preferences'
import Profile from './components/Profile'
import { fetchArticles } from './api'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // User Management State
  const [currentView, setCurrentView] = useState('login') // 'login', 'signup', 'preferences', 'feed', 'profile'
  const [users, setUsers] = useState([
    { username: 'admin', password: 'admin', firstName: 'Admin', lastName: 'User', hasPreferences: true }
  ])
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    if (isLoggedIn && currentView === 'feed') {
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
    }
  }, [isLoggedIn, currentView])

  const [showMenu, setShowMenu] = useState(false)

  const handleLogin = (username, password) => {
    const user = users.find(u => u.username === username && u.password === password)
    if (user) {
      setIsLoggedIn(true)
      setCurrentUser(user)
      if (user.hasPreferences) {
        setCurrentView('feed')
      } else {
        setCurrentView('preferences')
      }
      return true
    }
    return false
  }

  const handleSignup = (userData) => {
    // Check if username exists
    if (users.some(u => u.username === userData.username)) {
      alert('Username already exists')
      return
    }

    const newUser = { ...userData, hasPreferences: false }
    setUsers([...users, newUser])

    // Auto login after signup
    setIsLoggedIn(true)
    setCurrentUser(newUser)
    setCurrentView('preferences')
  }

  const handleSavePreferences = (prefs) => {
    // Update current user with preferences
    const updatedUser = { ...currentUser, ...prefs, hasPreferences: true }
    setCurrentUser(updatedUser)

    // Update user in users list
    setUsers(users.map(u => u.username === currentUser.username ? updatedUser : u))

    setCurrentView('feed')
  }

  const handleUpdateProfile = (updatedData) => {
    const updatedUser = { ...currentUser, ...updatedData }
    setCurrentUser(updatedUser)
    setUsers(users.map(u => u.username === currentUser.username ? updatedUser : u))
  }

  const handleChangePassword = (currentPassword, newPassword) => {
    if (currentUser.password !== currentPassword) {
      return false
    }
    const updatedUser = { ...currentUser, password: newPassword }
    setCurrentUser(updatedUser)
    setUsers(users.map(u => u.username === currentUser.username ? updatedUser : u))
    return true
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setCurrentUser(null)
    setArticles([])
    setLoading(true)
    setShowMenu(false)
    setCurrentView('login')
  }

  if (!isLoggedIn) {
    if (currentView === 'signup') {
      return <Signup onSignup={handleSignup} onSwitchToLogin={() => setCurrentView('login')} />
    }
    return <Login onLogin={handleLogin} onSwitchToSignup={() => setCurrentView('signup')} />
  }

  if (currentView === 'preferences') {
    return <Preferences onSave={handleSavePreferences} />
  }

  if (currentView === 'profile') {
    return (
      <Profile
        user={currentUser}
        onUpdateProfile={handleUpdateProfile}
        onChangePassword={handleChangePassword}
        onCancel={() => setCurrentView('feed')}
      />
    )
  }

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
        <button onClick={handleLogout} className="logout-button error-logout">Logout</button>
      </div>
    )
  }

  return (
    <div className="app-container">
      <div className="user-menu-container">
        <button
          className="user-button"
          onClick={() => setShowMenu(!showMenu)}
          aria-label="User Menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" />
          </svg>
        </button>
        {showMenu && (
          <div className="user-dropdown">
            <div className="menu-header">
              <span className="menu-username">{currentUser?.username}</span>
            </div>
            <div className="menu-divider"></div>
            <button onClick={() => {
              setShowMenu(false)
              setCurrentView('profile')
            }} className="menu-item">
              Edit Profile
            </button>
            <button onClick={() => {
              setShowMenu(false)
              setCurrentView('preferences')
            }} className="menu-item">
              Preferences
            </button>
            <button onClick={handleLogout} className="menu-item">
              Logout
            </button>
          </div>
        )}
      </div>
      {articles.map((article, index) => (
        <Article key={article.id || index} article={article} />
      ))}
    </div>
  )
}

export default App
