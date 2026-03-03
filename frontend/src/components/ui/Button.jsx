import React from 'react'
import { cn } from '../../utils/cn'

function Button({ as: Component = 'button', className = '', children, ...props }) {
  const componentProps = { ...props }
  if (Component !== 'button') {
    delete componentProps.type
  }

  return (
    <Component
      className={cn(
        'inline-flex min-h-10 items-center justify-center rounded-md bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed disabled:bg-slate-400 dark:disabled:bg-slate-600',
        className,
      )}
      {...componentProps}
    >
      {children}
    </Component>
  )
}

export default Button
