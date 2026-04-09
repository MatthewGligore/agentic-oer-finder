import React from 'react'
import { Outlet } from 'react-router-dom'
import SideNav from './SideNav'

function DashboardLayout() {
  return (
    <div className="dashboard-layout">
      <SideNav />
      <Outlet />
    </div>
  )
}

export default DashboardLayout
