import { useEffect, useState } from 'react'

export type ResponsiveExperience = {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
}

const mobileQuery = '(max-width: 767px)'
const tabletQuery = '(min-width: 768px) and (max-width: 1180px)'

function getMatches(query: string) {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia(query).matches
}

export function useResponsiveExperience(): ResponsiveExperience {
  const [state, setState] = useState<ResponsiveExperience>(() => {
    const isMobile = getMatches(mobileQuery)
    const isTablet = getMatches(tabletQuery)
    return { isMobile, isTablet, isDesktop: !isMobile && !isTablet }
  })

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined

    const mobileMedia = window.matchMedia(mobileQuery)
    const tabletMedia = window.matchMedia(tabletQuery)
    const update = () => {
      const isMobile = mobileMedia.matches
      const isTablet = tabletMedia.matches
      setState({ isMobile, isTablet, isDesktop: !isMobile && !isTablet })
    }

    update()
    mobileMedia.addEventListener('change', update)
    tabletMedia.addEventListener('change', update)
    return () => {
      mobileMedia.removeEventListener('change', update)
      tabletMedia.removeEventListener('change', update)
    }
  }, [])

  return state
}
