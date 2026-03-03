import React, { useState } from 'react'
import Card from './ui/Card'
import Input from './ui/Input'
import Button from './ui/Button'

function SearchForm({ onSubmit, isLoading }) {
  const [courseCode, setCourseCode] = useState('')
  const [term, setTerm] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (courseCode.trim()) {
      onSubmit(courseCode.trim().toUpperCase(), term.trim())
    }
  }

  return (
    <Card className="mx-auto max-w-2xl p-6 md:p-8">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="courseCode">Course Code</label>
          <Input
            type="text"
            id="courseCode"
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            placeholder="e.g., ENGL 1101"
            required
            disabled={isLoading}
          />
          <small className="mt-1.5 block text-xs text-slate-500 dark:text-slate-400">Enter course code (e.g., ENGL 1101, HIST 2111, ITEC 1001)</small>
        </div>

        <div className="mb-0">
          <label className="mb-2 block text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="term">Term (Optional)</label>
          <Input
            type="text"
            id="term"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="e.g., Fall 2025, Spring 2026"
            disabled={isLoading}
          />
        </div>

        <Button type="submit" className="w-full" disabled={isLoading || !courseCode.trim()}>
          {isLoading ? 'Searching...' : 'Search OER Resources'}
        </Button>
      </form>
    </Card>
  )
}

export default SearchForm
