"use client";

import { BookOpen, Search, Tag, TrendingUp } from "lucide-react";

export default function KnowledgePage() {
  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-100 text-green-700 text-sm font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          <span>Knowledge Management</span>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Knowledge Base
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Extract insights from historical analyses and build your team's collective wisdom.
        </p>
      </div>

      {/* Coming Soon Card */}
      <div className="glass rounded-2xl p-12 shadow-lg text-center">
        <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <BookOpen className="w-10 h-10 text-green-600" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-900 mb-3">
          Coming Soon
        </h2>
        <p className="text-slate-600 mb-8 max-w-md mx-auto">
          Knowledge base features are currently under development.
          Soon you'll be able to capture and organize insights from your analyses!
        </p>

        <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <Search className="w-8 h-8 text-blue-600 mb-3 mx-auto" />
            <h3 className="font-semibold text-slate-900 mb-2">Smart Search</h3>
            <p className="text-sm text-slate-600">
              Full-text search across all knowledge entries
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <Tag className="w-8 h-8 text-purple-600 mb-3 mx-auto" />
            <h3 className="font-semibold text-slate-900 mb-2">Categorization</h3>
            <p className="text-sm text-slate-600">
              Organize by tags, categories, and profiles
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 border border-slate-200">
            <TrendingUp className="w-8 h-8 text-green-600 mb-3 mx-auto" />
            <h3 className="font-semibold text-slate-900 mb-2">Insights</h3>
            <p className="text-sm text-slate-600">
              Extract patterns and trends from analyses
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
