/**
 * Utility functions for file operations
 */

/**
 * Download a file to the user's device
 *
 * @param content - File content as string
 * @param filename - Name of the file to download
 * @param mimeType - MIME type of the file
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Calculate percentage with safe division
 *
 * @param current - Current value
 * @param total - Total value
 * @returns Percentage rounded to nearest integer
 */
export function calculatePercentage(current: number, total: number): number {
  return total > 0 ? Math.round((current / total) * 100) : 0;
}

/**
 * Format seconds into human-readable time string
 *
 * @param seconds - Time in seconds
 * @returns Formatted time string (e.g., "2m 30s", "45s")
 */
export function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs}s`;
}
