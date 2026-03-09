"use client";

import { useAuth } from "@/contexts/AuthContext";
import {
  ImpersonationBanner,
  ImpersonationBannerSpacer,
} from "./ImpersonationBanner";
import {
  Calendar,
  ChevronDown,
  LogIn,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { MobileNav } from "./MobileNav";
import { navItems } from "./navItems";
import { UserMenu } from "./UserMenu";

/**
 * Number of user nav items shown directly in the top bar.
 * The rest go into a "More" dropdown to prevent overflow at 1440px.
 * 9 items keeps the bar comfortable at 1280px max-w-7xl minus logo/auth.
 */
const VISIBLE_COUNT = 9;

export function Navigation() {
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === "admin";

  // Split nav items: admin items for black bar, user items for white bar
  const adminNavItems = navItems.filter((item) => item.adminOnly);
  const userNavItems = navItems.filter((item) => !item.adminOnly);

  const primaryItems = userNavItems.slice(0, VISIBLE_COUNT);
  const overflowItems = userNavItems.slice(VISIBLE_COUNT);

  // Is any overflow item the current page?
  const overflowActive = overflowItems.some((item) => pathname === item.href);

  // Close dropdown on outside click
  useEffect(() => {
    if (!moreOpen) return;
    function handleClick(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [moreOpen]);

  // Close dropdown on route change
  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  return (
    <>
      {/* Impersonation Banner - shown above navigation when impersonating */}
      <ImpersonationBanner />
      <ImpersonationBannerSpacer />

      {/* Skip to main content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>

      {/* Admin Navigation Bar - shown above user bar when logged in as admin */}
      {isAdmin && (
        <nav className="bg-black" aria-label="Admin navigation">
          <div className="max-w-7xl mx-auto px-4">
            <div className="hidden md:flex items-center h-10 gap-1 overflow-x-auto">
              {adminNavItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={item.label}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? "bg-gray-700 text-white"
                        : "text-gray-300 hover:bg-gray-800 hover:text-white"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </nav>
      )}

      {/* User Navigation Bar - always shown */}
      <nav className="bg-white shadow-sm" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Left Side: Mobile Menu + Logo */}
            <div className="flex items-center gap-2">
              {/* Mobile Hamburger */}
              <MobileNav />

              {/* Logo */}
              <Link
                href="/"
                className="flex items-center gap-2"
                aria-label="Residency Scheduler home"
              >
                <Calendar
                  className="w-8 h-8 text-blue-600"
                  aria-hidden="true"
                />
                <span className="font-bold text-xl text-gray-900 hidden sm:block">
                  Residency Scheduler
                </span>
                <span className="font-bold text-xl text-gray-900 sm:hidden">
                  Scheduler
                </span>
              </Link>
            </div>

            {/* Desktop Navigation Links - hidden on mobile */}
            <div className="hidden md:flex items-center gap-0.5">
              {primaryItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={item.label}
                    className={`flex items-center gap-1.5 px-2 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                    {item.label}
                  </Link>
                );
              })}

              {/* "More" dropdown for overflow items */}
              {overflowItems.length > 0 && (
                <div className="relative" ref={moreRef}>
                  <button
                    type="button"
                    onClick={() => setMoreOpen((v) => !v)}
                    aria-expanded={moreOpen}
                    aria-haspopup="true"
                    className={`flex items-center gap-1 px-2 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                      overflowActive
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    More
                    <ChevronDown
                      className={`w-3.5 h-3.5 transition-transform ${moreOpen ? "rotate-180" : ""}`}
                      aria-hidden="true"
                    />
                  </button>

                  {moreOpen && (
                    <div className="absolute right-0 mt-1 w-48 rounded-md shadow-lg bg-white ring-1 ring-black/5 z-50 py-1">
                      {overflowItems.map((item) => {
                        const isActive = pathname === item.href;
                        const Icon = item.icon;

                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            aria-current={isActive ? "page" : undefined}
                            className={`flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                              isActive
                                ? "bg-blue-50 text-blue-700 font-medium"
                                : "text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <Icon className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                            {item.label}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Side: Auth Section */}
            <div className="flex items-center">
              <div className="md:ml-4 md:pl-4 md:border-l md:border-gray-200 flex items-center gap-3">
                {isLoading ? (
                  <span className="text-sm text-gray-400">...</span>
                ) : isAuthenticated && user ? (
                  <UserMenu />
                ) : (
                  <Link
                    href="/login"
                    aria-current={pathname === "/login" ? "page" : undefined}
                    aria-label="Login to your account"
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === "/login"
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    <LogIn className="w-4 h-4" aria-hidden="true" />
                    <span className="hidden sm:inline">Login</span>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>
    </>
  );
}
