import React, { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import SideNav from './SideNav'

function DashboardLayout() {
  const [isDesktop, setIsDesktop] = useState(() => window.matchMedia('(min-width: 901px)').matches)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 901px)')
    const onChange = (event) => setIsDesktop(event.matches)

    setIsDesktop(mediaQuery.matches)
    mediaQuery.addEventListener('change', onChange)

    return () => mediaQuery.removeEventListener('change', onChange)
  }, [])

  return (
    <div className="dashboard-layout">
      {isDesktop ? <SideNav /> : null}
      <Outlet />
    </div>
  )
}

export default DashboardLayout
