// Debug script to test query interpretation logic
const query = "How many packages have been upgrade in the last day?";
const normalizedQuery = query.toLowerCase().trim();

console.log("Original query:", query);
console.log("Normalized query:", normalizedQuery);

// Test isHealthQuery (fixed version)
const healthKeywords = ['health', 'status', 'running', 'operational', 'working'];
const healthWordBoundaries = ['\\bup\\b']; // Use word boundaries for short words like "up"

// Check regular keywords
const hasHealthKeyword = healthKeywords.some(keyword => normalizedQuery.includes(keyword));

// Check word boundary keywords
const hasHealthWordBoundary = healthWordBoundaries.some(pattern => {
  const regex = new RegExp(pattern, 'i');
  return regex.test(normalizedQuery);
});

const isHealthFixed = hasHealthKeyword || hasHealthWordBoundary;
console.log("isHealthQuery (fixed):", isHealthFixed, "- regular keywords:", healthKeywords.filter(k => normalizedQuery.includes(k)), "- word boundary match:", hasHealthWordBoundary);

// Test isPackageUpdateQuery
const packageKeywords = ['package', 'packages'];
const updateKeywords = ['update', 'updates', 'upgrade', 'upgraded', 'install', 'installed'];
const timeKeywords = ['day', 'days', 'week', 'weeks', 'month', 'months', 'last', 'recent', 'today', 'yesterday'];

const hasPackage = packageKeywords.some(keyword => normalizedQuery.includes(keyword));
const hasUpdate = updateKeywords.some(keyword => normalizedQuery.includes(keyword));
const hasTime = timeKeywords.some(keyword => normalizedQuery.includes(keyword));

console.log("Package keywords found:", packageKeywords.filter(k => normalizedQuery.includes(k)));
console.log("Update keywords found:", updateKeywords.filter(k => normalizedQuery.includes(k)));
console.log("Time keywords found:", timeKeywords.filter(k => normalizedQuery.includes(k)));
console.log("hasPackage:", hasPackage);
console.log("hasUpdate:", hasUpdate);
console.log("hasTime:", hasTime);

const isPackageUpdate = (hasPackage && hasUpdate) || (hasUpdate && hasTime);
console.log("isPackageUpdateQuery:", isPackageUpdate);

// Test isStatisticsQuery first part
console.log("isPackageUpdateQuery for stats exclusion:", isPackageUpdate);

const statsKeywords = ['statistics', 'stats', 'overview', 'summary', 'dashboard'];
const generalCountKeywords = ['total', 'count', 'how many'];

const hasGeneralCount = generalCountKeywords.some(keyword => normalizedQuery.includes(keyword));
const hasSpecificContext = normalizedQuery.includes('package') || normalizedQuery.includes('update') || normalizedQuery.includes('upgrade') || 
                          normalizedQuery.includes('host') || normalizedQuery.includes('day') || normalizedQuery.includes('week') || normalizedQuery.includes('month');

console.log("General count keywords found:", generalCountKeywords.filter(k => normalizedQuery.includes(k)));
console.log("hasGeneralCount:", hasGeneralCount);
console.log("hasSpecificContext:", hasSpecificContext);

const statsMatch = statsKeywords.some(keyword => normalizedQuery.includes(keyword)) || 
           (hasGeneralCount && !hasSpecificContext);

console.log("isStatisticsQuery (before package update exclusion):", statsMatch);
console.log("isStatisticsQuery (final):", statsMatch && !isPackageUpdate);
