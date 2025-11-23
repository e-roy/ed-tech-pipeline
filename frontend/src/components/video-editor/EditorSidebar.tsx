'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Menu,
  ChevronLeft,
  Add,
  FolderOpen,
  History,
  ContentCut,
  Home,
} from '@mui/icons-material';
import { colors } from './theme';

const DRAWER_WIDTH = 220;
const COLLAPSED_WIDTH = 48;

const navItems = [
  {
    title: 'Dashboard',
    url: '/dashboard',
    icon: Home,
  },
  {
    title: 'Create',
    url: '/dashboard/create',
    icon: Add,
  },
  {
    title: 'Assets',
    url: '/dashboard/assets',
    icon: FolderOpen,
  },
  {
    title: 'History',
    url: '/dashboard/history',
    icon: History,
  },
];

export function EditorSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Collapsed sidebar strip */}
      <Box
        sx={{
          width: COLLAPSED_WIDTH,
          bgcolor: colors.bg.paper,
          borderRight: `1px solid ${colors.border.subtle}`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 1,
          zIndex: 1,
        }}
      >
        <Tooltip title="Open Navigation" placement="right">
          <IconButton
            onClick={() => setOpen(true)}
            sx={{
              color: colors.text.secondary,
              '&:hover': {
                bgcolor: colors.bg.hover,
                color: colors.text.primary,
              },
            }}
          >
            <Menu />
          </IconButton>
        </Tooltip>

        <Divider sx={{ my: 1, width: '70%', bgcolor: colors.border.subtle }} />

        {/* Quick access icons */}
        {navItems.slice(0, 4).map((item) => (
          <Tooltip key={item.title} title={item.title} placement="right">
            <IconButton
              component={Link}
              href={item.url}
              sx={{
                color: colors.text.muted,
                my: 0.5,
                '&:hover': {
                  bgcolor: colors.bg.hover,
                  color: colors.text.primary,
                },
              }}
            >
              <item.icon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
        ))}
      </Box>

      {/* Expanded drawer */}
      <Drawer
        anchor="left"
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            bgcolor: colors.bg.paper,
            borderRight: `1px solid ${colors.border.subtle}`,
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1.5,
            borderBottom: `1px solid ${colors.border.subtle}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ContentCut sx={{ fontSize: 20, color: colors.primary.main }} />
            <Typography
              variant="subtitle1"
              sx={{
                color: colors.text.primary,
                fontWeight: 600,
              }}
            >
              Pipeline
            </Typography>
          </Box>
          <IconButton
            onClick={() => setOpen(false)}
            size="small"
            sx={{ color: colors.text.secondary }}
          >
            <ChevronLeft />
          </IconButton>
        </Box>

        {/* Navigation */}
        <List sx={{ flex: 1, py: 1 }}>
          {navItems.map((item) => (
            <ListItemButton
              key={item.title}
              component={Link}
              href={item.url}
              onClick={() => setOpen(false)}
              sx={{
                mx: 1,
                borderRadius: 1,
                '&:hover': {
                  bgcolor: colors.bg.hover,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <item.icon sx={{ fontSize: 20, color: colors.text.secondary }} />
              </ListItemIcon>
              <ListItemText
                primary={item.title}
                primaryTypographyProps={{
                  variant: 'body2',
                  sx: { color: colors.text.primary },
                }}
              />
            </ListItemButton>
          ))}
        </List>

        {/* Footer */}
        <Box
          sx={{
            p: 2,
            borderTop: `1px solid ${colors.border.subtle}`,
          }}
        >
          <Typography
            variant="caption"
            sx={{ color: colors.text.muted, display: 'block', textAlign: 'center' }}
          >
            Video Editor
          </Typography>
        </Box>
      </Drawer>
    </>
  );
}
