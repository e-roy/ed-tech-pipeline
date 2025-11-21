'use client';

import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import GlobalStyles from '@mui/material/GlobalStyles';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { editorTheme } from '@/components/video-editor/theme';

export default function EditingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppRouterCacheProvider options={{ enableCssLayer: true }}>
      <GlobalStyles
        styles={`
          @layer theme, base, mui, components, utilities;
        `}
      />
      <ThemeProvider theme={editorTheme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AppRouterCacheProvider>
  );
}
