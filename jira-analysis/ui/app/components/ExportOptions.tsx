"use client";

import { Download, FileText, Mail, BookOpen } from "lucide-react";
import { downloadFile, calculatePercentage } from "@/lib/utils";

interface ExportOptionsProps {
  reportData: {
    summary: {
      total: number;
      completed: number;
      errors: number;
      profiles: Record<string, number>;
    };
    reports: Array<{
      issue_key: string;
      profile: string;
      content: string;
      error?: string;
    }>;
  };
}

export default function ExportOptions({ reportData }: ExportOptionsProps) {
  const handleExportMarkdown = () => {
    let markdown = `# Batch Analysis Report\n\n`;
    markdown += `## Summary\n\n`;
    markdown += `- **Total Issues**: ${reportData.summary.total}\n`;
    markdown += `- **Completed**: ${reportData.summary.completed}\n`;
    markdown += `- **Errors**: ${reportData.summary.errors}\n`;
    markdown += `- **Success Rate**: ${calculatePercentage(reportData.summary.completed, reportData.summary.total)}%\n\n`;

    if (Object.keys(reportData.summary.profiles).length > 0) {
      markdown += `### Profile Distribution\n\n`;
      Object.entries(reportData.summary.profiles).forEach(([profile, count]) => {
        markdown += `- **${profile}**: ${count}\n`;
      });
      markdown += `\n`;
    }

    markdown += `## Individual Reports\n\n`;
    reportData.reports.forEach((report) => {
      markdown += `### ${report.issue_key} (${report.profile})\n\n`;
      if (report.error) {
        markdown += `**Error**: ${report.error}\n\n`;
      } else {
        markdown += `${report.content}\n\n`;
      }
      markdown += `---\n\n`;
    });

    downloadFile(
      markdown,
      `batch-analysis-${new Date().toISOString().split("T")[0]}.md`,
      "text/markdown"
    );
  };

  const handleExportJSON = () => {
    const json = JSON.stringify(reportData, null, 2);
    downloadFile(
      json,
      `batch-analysis-${new Date().toISOString().split("T")[0]}.json`,
      "application/json"
    );
  };

  const handleSaveToKnowledge = async () => {
    // TODO: Implement knowledge base save
    alert("Knowledge base integration coming soon!");
  };

  const handleEmailReport = () => {
    // TODO: Implement email functionality
    alert("Email functionality coming soon!");
  };

  return (
    <div className="glass rounded-2xl p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Export Options</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <button
          onClick={handleExportMarkdown}
          className="flex flex-col items-center gap-2 p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
        >
          <FileText className="w-6 h-6 text-blue-600" />
          <span className="text-sm font-medium text-slate-900">Markdown</span>
        </button>

        <button
          onClick={handleExportJSON}
          className="flex flex-col items-center gap-2 p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
        >
          <Download className="w-6 h-6 text-purple-600" />
          <span className="text-sm font-medium text-slate-900">JSON</span>
        </button>

        <button
          onClick={handleSaveToKnowledge}
          className="flex flex-col items-center gap-2 p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
        >
          <BookOpen className="w-6 h-6 text-green-600" />
          <span className="text-sm font-medium text-slate-900">Knowledge Base</span>
        </button>

        <button
          onClick={handleEmailReport}
          className="flex flex-col items-center gap-2 p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
        >
          <Mail className="w-6 h-6 text-indigo-600" />
          <span className="text-sm font-medium text-slate-900">Email</span>
        </button>
      </div>
    </div>
  );
}
