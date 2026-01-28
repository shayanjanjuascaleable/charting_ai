/**
 * Plotly localization utilities
 * Handles locale registration and chart text translation
 */

// Chart text translation mapping (English -> Arabic)
const chartTextTranslations: Record<string, string> = {
  // Common terms
  'Revenue': 'الإيرادات',
  'Region': 'المنطقة',
  'Regions': 'المناطق',
  'Account': 'حساب',
  'Accounts': 'الحسابات',
  'Lead': 'عميل محتمل',
  'Leads': 'العملاء المحتملون',
  'Opportunity': 'فرصة',
  'Opportunities': 'الفرص',
  'Contact': 'جهة اتصال',
  'Contacts': 'جهات الاتصال',
  'Status': 'الحالة',
  'Stage': 'المرحلة',
  'Source': 'المصدر',
  'Budget': 'الميزانية',
  'Value': 'القيمة',
  'Count': 'العدد',
  'Total': 'الإجمالي',
  'Average': 'المتوسط',
  'Sum': 'المجموع',
  'CreatedDate': 'تاريخ الإنشاء',
  'Created Date': 'تاريخ الإنشاء',
  'Date': 'التاريخ',
  'Month': 'الشهر',
  'Year': 'السنة',
  'Industry': 'الصناعة',
  'Role': 'الدور',
  'Name': 'الاسم',
  'Amount': 'المبلغ',
  'ExpectedCloseDate': 'تاريخ الإغلاق المتوقع',
  'Expected Close Date': 'تاريخ الإغلاق المتوقع',
  
  // Common phrases
  'by': 'حسب',
  'Total Revenue': 'إجمالي الإيرادات',
  'Total Value': 'إجمالي القيمة',
  'Top 10': 'أفضل 10',
  'Distribution': 'التوزيع',
  'Trends': 'الاتجاهات',
  'Performance': 'الأداء',
  'Growth': 'النمو',
  'Pipeline': 'خط الأنابيب',
  'Conversion': 'التحويل',
  'Funnel': 'القمع',
  'Revenue by': 'الإيرادات حسب',
  'Value by': 'القيمة حسب',
  'Count by': 'العدد حسب',
  'Average by': 'المتوسط حسب',
  'Sum by': 'المجموع حسب',
  'per': 'لكل',
  'over time': 'بمرور الوقت',
  'by month': 'حسب الشهر',
  'by year': 'حسب السنة',
  'by region': 'حسب المنطقة',
  'by industry': 'حسب الصناعة',
  'by status': 'حسب الحالة',
  'by stage': 'حسب المرحلة',
  'by source': 'حسب المصدر',
};

/**
 * Translate chart text labels (titles, axis labels, trace names)
 * Returns the translated string if found, otherwise returns original
 */
export const translateChartText = (text: string | undefined | null): string => {
  if (!text || typeof text !== 'string') return text || '';
  
  // Direct match
  if (chartTextTranslations[text]) {
    return chartTextTranslations[text];
  }
  
  // Try case-insensitive match
  const lowerText = text.toLowerCase();
  for (const [key, value] of Object.entries(chartTextTranslations)) {
    if (key.toLowerCase() === lowerText) {
      return value;
    }
  }
  
  // Try partial matches for common patterns
  // e.g., "Revenue by Region" -> "الإيرادات حسب المنطقة"
  let translated = text;
  for (const [key, value] of Object.entries(chartTextTranslations)) {
    const regex = new RegExp(`\\b${key}\\b`, 'gi');
    translated = translated.replace(regex, value);
  }
  
  return translated;
};

/**
 * Apply translations to Plotly chart JSON
 * Translates titles, axis labels, and trace names
 */
export const translateChartJson = (chartJson: any): any => {
  if (!chartJson) return chartJson;
  
  const translated = JSON.parse(JSON.stringify(chartJson)); // Deep clone
  
  // Translate layout title
  if (translated.layout?.title?.text) {
    translated.layout.title.text = translateChartText(translated.layout.title.text);
  }
  
  // Translate x-axis title
  if (translated.layout?.xaxis?.title?.text) {
    translated.layout.xaxis.title.text = translateChartText(translated.layout.xaxis.title.text);
  }
  
  // Translate y-axis title
  if (translated.layout?.yaxis?.title?.text) {
    translated.layout.yaxis.title.text = translateChartText(translated.layout.yaxis.title.text);
  }
  
  // Translate trace names
  if (Array.isArray(translated.data)) {
    translated.data = translated.data.map((trace: any) => {
      if (trace.name) {
        return {
          ...trace,
          name: translateChartText(trace.name),
        };
      }
      return trace;
    });
  }
  
  return translated;
};

/**
 * Initialize Plotly locale
 * Plotly.js-dist-min includes locale support, but we need to ensure it's available
 * The locale is set via the config prop in the Plot component
 */
export const initializePlotlyLocale = async (language: 'en' | 'ar'): Promise<void> => {
  // Plotly.js-dist-min includes built-in locale support
  // The locale is applied via the config.locale prop in the Plot component
  // No additional registration needed for basic locale support
  // For Arabic, Plotly will use 'ar' locale if available in the bundle
  
  // Note: plotly.js-dist-min may not include all locales by default
  // If Arabic locale is not available, charts will fall back to English
  // The chart text translation (translateChartJson) will still work
};

