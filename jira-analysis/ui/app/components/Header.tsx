"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, FileText, BookOpen } from "lucide-react";

export default function Header() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Deep Analysis", icon: Search },
    { href: "/reports", label: "Reports", icon: FileText },
    { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-50 glass border-b border-slate-200/50 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center">
              <span className="text-white font-bold text-xl">J</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Jira Analysis</h1>
              <p className="text-xs text-slate-500">AI-Powered Insights</p>
            </div>
          </div>

          <nav className="flex items-center gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive
                      ? "bg-blue-600 text-white shadow-md"
                      : "text-slate-600 hover:bg-white/50 hover:text-blue-600"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
