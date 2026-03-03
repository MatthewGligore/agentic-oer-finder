import React from 'react'
import { cn } from '../../utils/cn'

function Card({ className = '', children }) {
  return <div className={cn('rounded-lg bg-surface shadow-sm dark:border dark:border-slate-700/60', className)}>{children}</div>
}

export default Card
