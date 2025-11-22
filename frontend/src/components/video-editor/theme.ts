'use client';

import { createTheme, alpha } from '@mui/material/styles';

// Color palette constants
const colors = {
  // Base backgrounds with subtle depth
  bg: {
    darkest: '#0d0d0d',
    darker: '#141414',
    dark: '#1a1a1a',
    default: '#1e1e1e',
    paper: '#252525',
    elevated: '#2a2a2a',
    hover: '#303030',
  },
  // Accent colors
  primary: {
    main: '#3b82f6',
    light: '#60a5fa',
    dark: '#2563eb',
    glow: 'rgba(59, 130, 246, 0.3)',
  },
  secondary: {
    main: '#8b5cf6',
    light: '#a78bfa',
    dark: '#7c3aed',
  },
  // Track type colors
  tracks: {
    video: { main: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)', border: 'rgba(59, 130, 246, 0.3)' },
    audio: { main: '#22c55e', bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.3)' },
    text: { main: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)' },
  },
  // Status colors
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  // Text
  text: {
    primary: '#f1f5f9',
    secondary: '#94a3b8',
    muted: '#64748b',
  },
  // Borders
  border: {
    subtle: '#2a2a2a',
    default: '#3a3a3a',
    strong: '#4a4a4a',
  },
};

export const editorTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary.main,
      light: colors.primary.light,
      dark: colors.primary.dark,
    },
    secondary: {
      main: colors.secondary.main,
      light: colors.secondary.light,
      dark: colors.secondary.dark,
    },
    background: {
      default: colors.bg.dark,
      paper: colors.bg.paper,
    },
    divider: colors.border.default,
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
    },
    success: { main: colors.success },
    warning: { main: colors.warning },
    error: { main: colors.error },
    action: {
      hover: 'rgba(255, 255, 255, 0.06)',
      selected: alpha(colors.primary.main, 0.16),
      focus: alpha(colors.primary.main, 0.12),
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: 13,
    h6: {
      fontSize: '0.95rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    subtitle1: {
      fontSize: '0.875rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    subtitle2: {
      fontSize: '0.8rem',
      fontWeight: 600,
      letterSpacing: '0.01em',
      textTransform: 'uppercase',
      color: colors.text.secondary,
    },
    body2: {
      fontSize: '0.8125rem',
    },
    caption: {
      fontSize: '0.75rem',
      color: colors.text.muted,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 6,
  },
  shadows: [
    'none',
    '0 1px 2px rgba(0,0,0,0.3)',
    '0 2px 4px rgba(0,0,0,0.3)',
    '0 4px 8px rgba(0,0,0,0.3)',
    '0 6px 12px rgba(0,0,0,0.35)',
    '0 8px 16px rgba(0,0,0,0.35)',
    '0 12px 24px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
    '0 16px 32px rgba(0,0,0,0.4)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: `${colors.border.strong} ${colors.bg.darker}`,
          '&::-webkit-scrollbar': {
            width: 8,
            height: 8,
          },
          '&::-webkit-scrollbar-track': {
            background: colors.bg.darker,
          },
          '&::-webkit-scrollbar-thumb': {
            background: colors.border.strong,
            borderRadius: 4,
            '&:hover': {
              background: colors.text.muted,
            },
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          minWidth: 'auto',
          borderRadius: 6,
          transition: 'all 0.15s ease',
        },
        contained: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
          background: `linear-gradient(135deg, ${colors.primary.main} 0%, ${colors.primary.dark} 100%)`,
          '&:hover': {
            boxShadow: `0 4px 12px ${colors.primary.glow}`,
            background: `linear-gradient(135deg, ${colors.primary.light} 0%, ${colors.primary.main} 100%)`,
          },
        },
        outlined: {
          borderColor: colors.border.default,
          '&:hover': {
            borderColor: colors.primary.main,
            backgroundColor: alpha(colors.primary.main, 0.08),
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          transition: 'all 0.15s ease',
          '&:hover': {
            backgroundColor: colors.bg.hover,
          },
        },
        sizeSmall: {
          padding: 6,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: colors.bg.elevated,
          color: colors.text.primary,
          fontSize: '0.75rem',
          fontWeight: 500,
          padding: '6px 10px',
          borderRadius: 6,
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          border: `1px solid ${colors.border.subtle}`,
        },
        arrow: {
          color: colors.bg.elevated,
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          height: 4,
          '& .MuiSlider-rail': {
            backgroundColor: colors.border.default,
            opacity: 1,
          },
          '& .MuiSlider-track': {
            background: `linear-gradient(90deg, ${colors.primary.dark} 0%, ${colors.primary.main} 100%)`,
            border: 'none',
          },
        },
        thumb: {
          width: 14,
          height: 14,
          backgroundColor: colors.text.primary,
          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
          transition: 'all 0.15s ease',
          '&:hover, &.Mui-focusVisible': {
            boxShadow: `0 0 0 6px ${alpha(colors.primary.main, 0.2)}`,
          },
          '&.Mui-active': {
            boxShadow: `0 0 0 8px ${alpha(colors.primary.main, 0.3)}`,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: colors.bg.darker,
            transition: 'all 0.15s ease',
            '& fieldset': {
              borderColor: colors.border.subtle,
              transition: 'all 0.15s ease',
            },
            '&:hover fieldset': {
              borderColor: colors.border.strong,
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.primary.main,
              borderWidth: 1,
            },
          },
          '& .MuiInputLabel-root': {
            color: colors.text.muted,
            fontSize: '0.8125rem',
          },
          '& .MuiInputBase-input': {
            fontSize: '0.8125rem',
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: colors.bg.darker,
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.border.subtle,
            transition: 'all 0.15s ease',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.border.strong,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.primary.main,
            borderWidth: 1,
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.bg.elevated,
          border: `1px solid ${colors.border.subtle}`,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontSize: '0.8125rem',
          '&:hover': {
            backgroundColor: colors.bg.hover,
          },
          '&.Mui-selected': {
            backgroundColor: alpha(colors.primary.main, 0.16),
            '&:hover': {
              backgroundColor: alpha(colors.primary.main, 0.24),
            },
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: 36,
        },
        indicator: {
          height: 2,
          borderRadius: 1,
          background: `linear-gradient(90deg, ${colors.primary.dark} 0%, ${colors.primary.main} 100%)`,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          minHeight: 36,
          fontSize: '0.8125rem',
          fontWeight: 500,
          textTransform: 'none',
          transition: 'all 0.15s ease',
          '&.Mui-selected': {
            color: colors.text.primary,
          },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: colors.border.subtle,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.bg.paper,
          border: `1px solid ${colors.border.subtle}`,
          boxShadow: '0 24px 48px rgba(0,0,0,0.5)',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          height: 6,
          borderRadius: 3,
          backgroundColor: colors.bg.darker,
        },
        bar: {
          borderRadius: 3,
          background: `linear-gradient(90deg, ${colors.primary.dark} 0%, ${colors.primary.main} 100%)`,
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          marginBottom: 2,
          transition: 'all 0.15s ease',
          '&:hover': {
            backgroundColor: colors.bg.hover,
          },
          '&.Mui-selected': {
            backgroundColor: alpha(colors.primary.main, 0.16),
            '&:hover': {
              backgroundColor: alpha(colors.primary.main, 0.24),
            },
          },
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          borderColor: colors.border.subtle,
          color: colors.text.secondary,
          transition: 'all 0.15s ease',
          '&:hover': {
            backgroundColor: colors.bg.hover,
          },
          '&.Mui-selected': {
            backgroundColor: alpha(colors.primary.main, 0.2),
            color: colors.primary.light,
            borderColor: colors.primary.main,
            '&:hover': {
              backgroundColor: alpha(colors.primary.main, 0.3),
            },
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        standardError: {
          backgroundColor: alpha(colors.error, 0.15),
          color: colors.text.primary,
        },
        standardSuccess: {
          backgroundColor: alpha(colors.success, 0.15),
          color: colors.text.primary,
        },
      },
    },
  },
});

// Export color constants for use in components
export { colors };
