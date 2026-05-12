import type { ReactNode } from 'react'

type DesktopLayoutProps = {
  children: ReactNode
}

export function DesktopLayout({ children }: DesktopLayoutProps) {
  return <>{children}</>
}
