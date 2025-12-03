import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import './App.css'
import Article from './components/Article'
import Login from './components/Login'
import Signup from './components/Signup'
import Onboarding from './components/Onboarding'
import Preferences from './components/Preferences'
import Profile from './components/Profile'
import { fetchArticles, login } from './api'

function App() {
  console.log('App rendering');
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('token');
    if (token) {
        setIsLoggedIn(true);
        // Ideally we would fetch user profile here to get name/preferences status
        // For now, we'll assume if they have a token they are logged in.
        // We might need to handle expired tokens.
        setCurrentUser({ email: 'User' }); // Placeholder
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
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
    } else {
        setLoading(false);
    }
  }, [isLoggedIn])

  const [showMenu, setShowMenu] = useState(false)

  const handleLogin = async (email, password) => {
    try {
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        setIsLoggedIn(true);
        setCurrentUser({ email: email }); // We could decode token or fetch profile
        
        // We don't know if they have preferences yet without fetching profile.
        // For now, let's assume they might need to go to onboarding if it's a new signup flow,
        // but typically login goes to home. 
        // If we want to force onboarding, we need a way to check.
        // Let's just go to home for now.
        navigate('/');
        return true;
    } catch (err) {
        console.error("Login failed", err);
        throw err;
    }
  }

  // Signup is handled in Signup component directly calling api.signup

  const handleSavePreferences = (prefs) => {
    // This is now handled by Onboarding component calling initiateUser
    // But if we have a separate preferences page, it might use a different API.
    // For now, let's just navigate.
    navigate('/')
  }

  const handleUpdateProfile = (updatedData) => {
    // Placeholder
    const updatedUser = { ...currentUser, ...updatedData }
    setCurrentUser(updatedUser)
  }

  const handleChangePassword = (currentPassword, newPassword) => {
    // Placeholder
    return true
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false)
    setCurrentUser(null)
    setArticles([])
    setLoading(true)
    setShowMenu(false)
    navigate('/login')
  }

  const ProtectedRoute = ({ children }) => {
    if (!isLoggedIn) {
      return <Navigate to="/login" />
    }
    return children
  }

  return (
    <div className="app-container">
      {isLoggedIn && (
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
                navigate('/profile')
              }} className="menu-item">
                Edit Profile
              </button>
              <button onClick={() => {
                setShowMenu(false)
                navigate('/preferences')
              }} className="menu-item">
                Preferences
              </button>
              <button onClick={handleLogout} className="menu-item">
                Logout
              </button>
            </div>
          )}
        </div>
      )}

      <Routes>
        <Route path="/login" element={
          !isLoggedIn ? 
          <Login onLogin={handleLogin} onSwitchToSignup={() => navigate('/signup')} /> : 
          <Navigate to="/" />
        } />
        
        <Route path="/signup" element={
          !isLoggedIn ? 
          <Signup onSwitchToLogin={() => navigate('/login')} /> : 
          <Navigate to="/" />
        } />

        <Route path="/onboarding" element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        } />

        <Route path="/preferences" element={
          <ProtectedRoute>
            <Preferences onSave={handleSavePreferences} initialPreferences={currentUser} />
          </ProtectedRoute>
        } />

        <Route path="/profile" element={
          <ProtectedRoute>
            <Profile
              user={currentUser}
              onUpdateProfile={handleUpdateProfile}
              onChangePassword={handleChangePassword}
              onCancel={() => navigate('/')}
            />
          </ProtectedRoute>
        } />

        <Route path="/" element={
          <ProtectedRoute>
            {loading ? (
              <div className="loading-container">
                <p>Loading articles...</p>
              </div>
            ) : error ? (
              <div className="error-container">
                <p>{error}</p>
                <button onClick={handleLogout} className="logout-button error-logout">Logout</button>
              </div>
            ) : (
              <div>
                {articles.map((article, index) => (
                  <Article key={article.id || index} article={article} />
                ))}
              </div>
            )}
          </ProtectedRoute>
        } />
      </Routes>
    </div>
  )
}

export default App
