import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import './App.css'
import Article from './components/Article'
import Login from './components/Login'
import Signup from './components/Signup'
import Onboarding from './components/Onboarding'
import Preferences from './components/Preferences'
import Profile from './components/Profile'
import { fetchArticles, login, fetchCurrentUser } from './api'

function App() {
  console.log('App rendering');
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate();
  const location = useLocation();

  const [currentUser, setCurrentUser] = useState(null)

  // Pagination State
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [isFetchingMore, setIsFetchingMore] = useState(false);

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('token');
    if (token) {
      // Fetch user profile to check onboarding status
      fetchCurrentUser()
        .then(user => {
          setIsLoggedIn(true);
          setCurrentUser(user);
          if (!user.is_onboarded) {
            navigate('/onboarding');
          }
        })
        .catch(err => {
          console.error("Failed to fetch user", err);
          // If token invalid, logout
          handleLogout();
        });
    } else {
      setLoading(false);
    }
  }, []); // Run once on mount

  const loadArticles = async (currentPage = 0, isRefresh = false) => {
    if (!hasMore && !isRefresh) return;

    try {
      if (currentPage === 0) {
        setLoading(true);
        setError(null);
      } else {
        setIsFetchingMore(true);
      }

      const limit = 20;
      const skip = currentPage * limit;
      const newArticles = await fetchArticles(skip, limit);

      if (newArticles.length < limit) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }

      if (currentPage === 0) {
        setArticles(newArticles);
      } else {
        setArticles(prev => [...prev, ...newArticles]);
      }
    } catch (err) {
      console.error(err);
      if (currentPage === 0) {
        setError('Failed to load articles. Please try logging in again.');
      }
    } finally {
      setLoading(false);
      setIsFetchingMore(false);
    }
  };

  // Initial Fetch on Login
  useEffect(() => {
    if (isLoggedIn) {
      if (currentUser && !currentUser.is_onboarded && location.pathname !== '/onboarding') {
        navigate('/onboarding');
        setLoading(false);
        return;
      }
      // Reset logic
      setPage(0);
      setHasMore(true);
      loadArticles(0, true);
    } else {
      setLoading(false);
    }
  }, [isLoggedIn, currentUser, location.pathname]);

  // Scroll Listener for Infinite Scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerHeight + document.documentElement.scrollTop + 1 >= document.documentElement.scrollHeight) {
        if (hasMore && !isFetchingMore && !loading) {
          const nextPage = page + 1;
          setPage(nextPage);
          loadArticles(nextPage);
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [hasMore, isFetchingMore, loading, page]);

  const [showMenu, setShowMenu] = useState(false)

  const handleLogin = async (email, password) => {
    try {
      setError(null);
      setLoading(true);
      const data = await login(email, password);
      localStorage.setItem('token', data.access_token);

      // Fetch user details to check onboarding
      const user = await fetchCurrentUser();
      setIsLoggedIn(true);
      setCurrentUser(user);

      if (!user.is_onboarded) {
        navigate('/onboarding');
      } else {
        navigate('/');
      }
      return true;
    } catch (err) {
      console.error("Login failed", err);
      setError("Login failed. Please check your credentials.");
      throw err;
    } finally {
      setLoading(false);
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
    setError(null) // Clear error state on logout
    setLoading(false) // No need to load anything
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
                {isFetchingMore && <p style={{ textAlign: 'center', padding: '1rem', color: '#666' }}>Loading more articles...</p>}
                {!hasMore && articles.length > 0 && <p style={{ textAlign: 'center', padding: '1rem', color: '#666' }}>You've reached the end of the feed.</p>}
              </div>
            )}
          </ProtectedRoute>
        } />
      </Routes>
    </div>
  )
}

export default App
