import { useState, useEffect, useRef, useCallback } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
// import './App.css'
import './AppModern.css'
import Article from './components/Article'
import SkeletonArticle from './components/SkeletonArticle'
import Login from './components/Login'
import Signup from './components/Signup'
import Onboarding from './components/Onboarding'
import Preferences from './components/Preferences'
import Profile from './components/Profile'
import DailySummary from './components/DailySummary'
import PreferenceUpdateToast from './components/PreferenceUpdateToast'
import { fetchArticles, login, fetchCurrentUser, fetchReadHistory, fetchPreferences } from './api'

const ProtectedRoute = ({ isLoggedIn, children }) => {
  if (!isLoggedIn) {
    return <Navigate to="/login" />
  }
  return children
}

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
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' or 'read'


  // Preference toast state
  const [showPreferenceToast, setShowPreferenceToast] = useState(false);
  const [oldPreferences, setOldPreferences] = useState(null);
  const [newPreferences, setNewPreferences] = useState(null);

  // Learning process visibility toggle
  const [showLearningProcess, setShowLearningProcess] = useState(() => {
    const saved = localStorage.getItem('showLearningProcess');
    return saved !== null ? saved === 'true' : true; // Default to true
  });

  // Daily Summary Generation State (Lifted for persistence)
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  // Initial Mount Effect - Check Token
  useEffect(() => {
    console.log("App mounted. Checking token...");
    const token = localStorage.getItem('token');
    if (token) {
      console.log("Token found. Fetching user...");
      fetchCurrentUser()
        .then(user => {
          console.log("User fetched successfully", user.id);
          setIsLoggedIn(true);
          setCurrentUser(user);
          if (!user.is_onboarded) {
            console.log("User not onboarded. Redirecting...");
            navigate('/onboarding');
          }
        })
        .catch(err => {
          console.error("Failed to fetch user (401?)", err);
          handleLogout();
        });
    } else {
      console.log("No token found.");
      setLoading(false);
    }
  }, []);

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
      let newArticles = [];

      if (activeTab === 'read') {
        newArticles = await fetchReadHistory(skip, limit);
      } else {
        newArticles = await fetchArticles(skip, limit);
      }

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

  // Initial Fetch on Login / Tab Change
  useEffect(() => {
    if (isLoggedIn) {
      if (currentUser && !currentUser.is_onboarded && location.pathname !== '/onboarding') {
        navigate('/onboarding');
        setLoading(false);
        return;
      }
      // Reset logic
      // Only reload articles if we are on Feed (/)
      if (location.pathname === '/') {
        setPage(0);
        setHasMore(true);
        loadArticles(0, true);
      } else {
        setLoading(false);
      }
    } else {
      // If not logged in, loading handled by Mount Effect
    }
  }, [isLoggedIn, currentUser, location.pathname, activeTab]);

  const containerRef = useRef(null);
  const lastScrollTopRef = useRef(0);

  // Scroll Listener for Infinite Scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    lastScrollTopRef.current = container.scrollTop; // Initialize on effect run

    const handleScroll = () => {
      if (isFetchingMore || !hasMore) return;

      const currentScrollTop = container.scrollTop;
      const scrollDelta = Math.abs(currentScrollTop - lastScrollTopRef.current);

      // Hide toast if scrolled more than 400px (significant navigation)
      if (showPreferenceToast && scrollDelta > 400) {
        setShowPreferenceToast(false);
      }

      // Update last scroll position (debounce or use interval if needed, but simple assignment is okay here)
      // Actually, we want to track delta relative to when the toast appeared?
      // No, just relative to last scroll event might be too small?
      // Wait, scroll event fires rapidly. Delta between events is small.
      // We need to track delta relative to a start position or accumulate it?

      // Let's compare to lastScrollTop but update lastScrollTop less frequently?
      // Or simply: check if scrollTop moved significantly since toast appeared?
      // Too complex for now. Let's strictly check if scrollTop differs from a stored "toastShownAt" position?
      // For now, let's just use a simpler heuristic: If scroll velocity is high?

      // Alternative: Just hide on ANY scroll > 50px to allow reading adjustment but hide on navigation.
      if (showPreferenceToast && scrollDelta > 50) {
        setShowPreferenceToast(false);
      }

      lastScrollTopRef.current = currentScrollTop;

      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;

      if (scrollTop + clientHeight >= scrollHeight - 100) {
        setIsFetchingMore(true);
        setPage(prevPage => prevPage + 1);
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [isFetchingMore, hasMore, showPreferenceToast]);

  const [showMenu, setShowMenu] = useState(false)

  const handleLogin = async (email, password) => {
    try {
      console.log("Handling login...");
      setError(null);
      setLoading(true);
      const data = await login(email, password);
      console.log("Login successful. Token:", data.access_token ? "Yes" : "No");
      localStorage.setItem('token', data.access_token);

      const user = await fetchCurrentUser();
      console.log("User fetched:", user.id);
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

  const handleSavePreferences = (prefs) => {
    navigate('/')
  }

  const handleUpdateProfile = (updatedData) => {
    const updatedUser = { ...currentUser, ...updatedData }
    setCurrentUser(updatedUser)
  }

  const handleOnboardingComplete = async () => {
    // Refresh user to get updated is_onboarded status
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
      navigate('/');
    } catch (err) {
      console.error("Failed to refresh user after onboarding", err);
    }
  }



  const handleLogout = () => {
    console.log("Logging out...");
    localStorage.removeItem('token');
    setIsLoggedIn(false)
    setCurrentUser(null)
    setArticles([])
    setError(null)
    setLoading(false)
    setShowMenu(false)
    navigate('/login')
  }

  const handleArticleInteraction = useCallback(async (type) => {
    console.log(`Article interaction: ${type}`);

    // Fetch preferences BEFORE the interaction
    try {
      const beforePrefs = await fetchPreferences();
      setOldPreferences(beforePrefs);

      // Wait for backend to process the interaction (give it time to update)
      setTimeout(async () => {
        try {
          const afterPrefs = await fetchPreferences();
          setNewPreferences(afterPrefs);
          setShowPreferenceToast(true);

          // Reset toast after a delay
          setTimeout(() => {
            setShowPreferenceToast(false);
          }, 4500);
        } catch (err) {
          console.error("Failed to fetch updated preferences for toast", err);
        }
      }, 800); // Delay to let backend process the interaction
    } catch (err) {
      console.error("Failed to fetch initial preferences for toast", err);
    }
  }, []);

  const toggleLearningProcess = () => {
    const newValue = !showLearningProcess;
    setShowLearningProcess(newValue);
    localStorage.setItem('showLearningProcess', String(newValue));
  }

  return (
    <div className="app-container" ref={containerRef}>
      <Routes>
        <Route path="/login" element={
          !isLoggedIn ?
            <Login onLogin={handleLogin} onSwitchToSignup={() => navigate('/signup')} /> :
            <Navigate to="/" />
        } />

        <Route path="/signup" element={
          !isLoggedIn ?
            <Signup onSwitchToLogin={() => navigate('/login')} onAutoLogin={handleLogin} /> :
            <Navigate to="/" />
        } />

        <Route path="/onboarding" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}>
            <Onboarding onOnboardingComplete={handleOnboardingComplete} />
          </ProtectedRoute>
        } />

        <Route path="/preferences" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}>
            <Preferences onSave={handleSavePreferences} initialPreferences={currentUser} />
          </ProtectedRoute>
        } />

        <Route path="/profile" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}>
            <Profile
              user={currentUser}
              onUpdateProfile={handleUpdateProfile}
              onCancel={() => navigate('/')}
            />
          </ProtectedRoute>
        } />

        <Route path="/" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}>
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
                <div className="feed-tabs">
                  <div>
                    <button
                      className={`tab-button ${activeTab === 'feed' ? 'active' : ''}`}
                      onClick={() => {
                        if (activeTab !== 'feed') {
                          setActiveTab('feed');
                          setArticles([]);
                          setLoading(true);
                        }
                      }}
                    >
                      For You
                    </button>
                    <button
                      className={`tab-button ${activeTab === 'read' ? 'active' : ''}`}
                      onClick={() => {
                        if (activeTab !== 'read') {
                          setActiveTab('read');
                          setArticles([]);
                          setLoading(true);
                        }
                      }}
                    >
                      Read History
                    </button>
                    <button
                      className={`tab-button ${activeTab === 'daily' ? 'active' : ''}`}
                      onClick={() => {
                        if (activeTab !== 'daily') {
                          setActiveTab('daily');
                          setArticles([]);
                          // setLoading(false); // DailySummary handles its own loading
                        }
                      }}
                    >
                      Daily Summary
                    </button>
                  </div>

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
                          <div className="menu-divider"></div>
                          <button
                            onClick={toggleLearningProcess}
                            className="menu-item menu-item-toggle"
                          >
                            <span>Show Learning Process</span>
                            <span className={`toggle-indicator ${showLearningProcess ? 'active' : ''}`}>
                              {showLearningProcess ? '✓' : ''}
                            </span>
                          </button>
                          <div className="menu-divider"></div>
                          <button onClick={handleLogout} className="menu-item">
                            Logout
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {activeTab === 'daily' ? (
                  <DailySummary
                    user={currentUser}
                    generating={isGeneratingSummary}
                    setGenerating={setIsGeneratingSummary}
                  />
                ) : (
                  <>
                    {articles.length === 0 && !loading && !error && (
                      <div className="empty-state">
                        {activeTab === 'read' ? "You haven't read any articles yet." : "No articles found."}
                      </div>
                    )}

                    {articles.map((article, index) => (
                      <Article key={article.id || index} article={article} onInteraction={handleArticleInteraction} />
                    ))}
                  </>
                )}
                {isFetchingMore && (
                  <>
                    <SkeletonArticle />
                    <SkeletonArticle />
                    <SkeletonArticle />
                  </>
                )}
                {!hasMore && articles.length > 0 && <p style={{ textAlign: 'center', padding: '1rem', color: '#666' }}>You've reached the end of the feed.</p>}
              </div>
            )}
          </ProtectedRoute>
        } />
      </Routes>
      {/* Preference Update Toast - only show if enabled */}
      {showLearningProcess && (
        <PreferenceUpdateToast
          show={showPreferenceToast}
          oldPreferences={oldPreferences}
          newPreferences={newPreferences}
        />
      )}
    </div>
  )
}

export default App
