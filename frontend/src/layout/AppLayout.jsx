import React from 'react'
import { Outlet } from 'react-router-dom'
import TopNav from './TopNav'

function AppLayout() {
  return (
    <div className="app-root">
      <TopNav />
      <Outlet />
    </div>
  )
}

export default AppLayout
