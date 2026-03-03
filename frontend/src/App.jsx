import React, { useEffect, useState } from 'react'
import SearchForm from './components/SearchForm'
import Results from './components/Results'
import oerAPI from './services/oerAPI'

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const useDark = storedTheme ? storedTheme === 'dark' : prefersDark
    setIsDarkMode(useDark)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode)
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  const handleSearch = async (courseCode, term) => {
    setIsLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await oerAPI.search(courseCode, term)
      setResults(data)
    } catch (err) {
      setError(
        err.error || 'An error occurred while searching for OER resources. Please try again.'
      )
      console.error('Search error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-app-100 to-app-200 text-slate-900 dark:text-slate-100">
      <header className="relative bg-gradient-to-br from-brand-600 to-brand-700 px-6 py-10 text-center text-white shadow-md md:px-8 md:py-12">
        <button
          type="button"
          onClick={() => setIsDarkMode((prev) => !prev)}
          className="absolute right-4 top-4 rounded-md bg-white/20 px-3 py-1.5 text-xs font-medium text-white backdrop-blur transition hover:bg-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 md:right-6 md:top-6 md:text-sm"
          aria-label="Toggle dark mode"
        >
          {isDarkMode ? '☀️ Light' : '🌙 Dark'}
        </button>
        <h1 className="mb-2 text-4xl font-bold md:text-5xl">Agentic OER Finder</h1>
        <p className="text-base text-brand-50/95 md:text-lg">
          AI-Powered Open Educational Resources Finder
        </p>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-8 md:px-6 md:py-10 lg:px-8">
        <section className="mb-10">
          <h2 className="mb-6 text-center text-2xl font-semibold tracking-tight text-slate-800 dark:text-slate-100 md:text-3xl">
            Find OER Resources for Your Course
          </h2>
          <SearchForm onSubmit={handleSearch} isLoading={isLoading} />
        </section>

        {isLoading && (
          <section className="mb-8 rounded-lg bg-surface p-10 shadow-sm dark:border dark:border-slate-700/60">
            <div className="flex flex-col items-center justify-center gap-4">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
              <p className="text-sm text-slate-600 dark:text-slate-300 md:text-base">Searching for OER resources... This may take a minute.</p>
            </div>
          </section>
        )}

        {error && (
          <section className="mb-8">
            <div className="rounded-md border-l-4 border-red-500 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm dark:bg-red-950/40 dark:text-red-300 md:text-base">
              {error}
            </div>
          </section>
        )}

        {!isLoading && results && (
          <section className="mb-10">
            <Results data={results} />
          </section>
        )}
      </main>

      <footer className="mt-auto bg-slate-800 px-6 py-8 text-center text-slate-100 dark:bg-slate-950">
        <p className="text-sm">Agentic OER Finder</p>
        <p className="mt-2">
          <a className="text-brand-100 hover:underline dark:text-brand-50" href="/api/stats" target="_blank" rel="noopener noreferrer">
            View Usage Statistics
          </a>
        </p>
      </footer>
    </div>
  )
}

export default App
