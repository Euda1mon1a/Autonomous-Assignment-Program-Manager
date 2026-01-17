'use client'

import { useState, useCallback } from 'react'
import { Copy, Check, Link as LinkIcon, Share2 } from 'lucide-react'

interface CopyToClipboardProps {
  /** Text to copy */
  text: string
  /** Label shown on button */
  label?: string
  /** Show the text in the button */
  showText?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Style variant */
  variant?: 'default' | 'ghost' | 'outline'
  /** Icon to show (copy, link, or share) */
  icon?: 'copy' | 'link' | 'share'
  /** Callback on successful copy */
  onCopy?: () => void
  /** Additional CSS classes */
  className?: string
}

/**
 * Copy to Clipboard Button
 *
 * A versatile button that copies text to the clipboard with visual feedback.
 * Supports different sizes, variants, and icons.
 */
export function CopyToClipboard({
  text,
  label,
  showText = false,
  size = 'md',
  variant = 'ghost',
  icon = 'copy',
  onCopy,
  className = '',
}: CopyToClipboardProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      onCopy?.()

      // Reset after 2 seconds
      setTimeout(() => setCopied(false), 2000)
    } catch (_error) {
      // console.error('Failed to copy to clipboard:', _error)

      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        setCopied(true)
        onCopy?.()
        setTimeout(() => setCopied(false), 2000)
      } finally {
        document.body.removeChild(textArea)
      }
    }
  }, [text, onCopy])

  const sizeClasses = {
    sm: 'p-1 text-xs',
    md: 'p-1.5 text-sm',
    lg: 'p-2 text-base',
  }

  const variantClasses = {
    default: 'bg-blue-600 text-white hover:bg-blue-700',
    ghost: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
  }

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  const IconComponent = icon === 'link' ? LinkIcon : icon === 'share' ? Share2 : Copy

  return (
    <button
      onClick={handleCopy}
      role="button"
      className={`
        inline-flex items-center gap-1.5 rounded-md transition-all
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${copied ? 'text-green-600 bg-green-50 hover:bg-green-50' : ''}
        ${className}
      `}
      title={copied ? 'Copied!' : label || 'Copy to clipboard'}
      aria-label={copied ? 'Copied!' : label || 'Copy to clipboard'}
    >
      {copied ? (
        <Check className={iconSizes[size]} />
      ) : (
        <IconComponent className={iconSizes[size]} />
      )}
      {(label || showText) && (
        <span className={copied ? 'text-green-600' : ''}>
          {copied ? 'Copied!' : label || text.slice(0, 20) + (text.length > 20 ? '...' : '')}
        </span>
      )}
    </button>
  )
}

/**
 * Copy URL Button - copies the current page URL
 */
export function CopyUrlButton({
  label = 'Copy Link',
  size = 'sm',
  variant = 'ghost',
  className = '',
  onCopy,
}: Omit<CopyToClipboardProps, 'text' | 'icon'>) {
  const [url, setUrl] = useState('')

  // Get current URL on mount (client-side only)
  if (typeof window !== 'undefined' && !url) {
    setUrl(window.location.href)
  }

  return (
    <CopyToClipboard
      text={url}
      label={label}
      size={size}
      variant={variant}
      icon="link"
      onCopy={onCopy}
      className={className}
    />
  )
}

/**
 * Copy with Input Field - shows the text being copied
 */
export function CopyInputField({
  value,
  label,
  onCopy,
  className = '',
}: {
  value: string
  label?: string
  onCopy?: () => void
  className?: string
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      onCopy?.()
      setTimeout(() => setCopied(false), 2000)
    } catch (_error) {
      // console.error('Failed to copy:', _error)
    }
  }, [value, onCopy])

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={value}
          readOnly
          className="flex-1 px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm text-gray-700 font-mono"
          onClick={(e) => (e.target as HTMLInputElement).select()}
        />
        <button
          onClick={handleCopy}
          role="button"
          className={`
            p-2 rounded-lg transition-all
            ${copied
              ? 'bg-green-100 text-green-600'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }
          `}
          title={copied ? 'Copied!' : 'Copy'}
          aria-label={copied ? 'Copied!' : 'Copy to clipboard'}
        >
          {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
        </button>
      </div>
    </div>
  )
}

/**
 * Share Button - uses native share API if available, falls back to copy
 */
export function ShareButton({
  title,
  text,
  url,
  size = 'md',
  variant = 'ghost',
  label = 'Share',
  className = '',
}: {
  title?: string
  text?: string
  url?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'ghost' | 'outline'
  label?: string
  className?: string
}) {
  const [shared, setShared] = useState(false)

  const handleShare = useCallback(async () => {
    const shareUrl = url || (typeof window !== 'undefined' ? window.location.href : '')

    // Try native share API first
    if (navigator.share) {
      try {
        await navigator.share({
          title: title || document.title,
          text,
          url: shareUrl,
        })
        setShared(true)
        setTimeout(() => setShared(false), 2000)
        return
      } catch (error) {
        // User cancelled or share failed, fall through to copy
        if ((error as Error).name === 'AbortError') return
      }
    }

    // Fallback to clipboard copy
    try {
      await navigator.clipboard.writeText(shareUrl)
      setShared(true)
      setTimeout(() => setShared(false), 2000)
    } catch (_error) {
      // console.error('Share failed:', _error)
    }
  }, [title, text, url])

  const sizeClasses = {
    sm: 'p-1 text-xs',
    md: 'p-1.5 text-sm',
    lg: 'p-2 text-base',
  }

  const variantClasses = {
    default: 'bg-blue-600 text-white hover:bg-blue-700',
    ghost: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
  }

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  return (
    <button
      onClick={handleShare}
      role="button"
      className={`
        inline-flex items-center gap-1.5 rounded-md transition-all
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${shared ? 'text-green-600 bg-green-50' : ''}
        ${className}
      `}
      title={shared ? 'Shared!' : label}
      aria-label={shared ? 'Shared!' : label}
    >
      {shared ? (
        <Check className={iconSizes[size]} />
      ) : (
        <Share2 className={iconSizes[size]} />
      )}
      {label && <span>{shared ? 'Shared!' : label}</span>}
    </button>
  )
}
