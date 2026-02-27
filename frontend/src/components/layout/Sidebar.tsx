import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  BarChart3,
  Bell,
  ChevronDown,
  Search,
  TrendingUp,
  Server,
  Building2,
  LayoutDashboard,
  Settings,
  Shield,
  Radar,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavChild {
  path: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

interface NavGroup {
  label: string
  icon: React.ComponentType<{ className?: string }>
  children: NavChild[]
}

type NavItem = NavChild | NavGroup

function isGroup(item: NavItem): item is NavGroup {
  return 'children' in item
}

const navigation: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/keywords', label: 'Mots-clés', icon: Search },
  {
    label: 'Analyses',
    icon: TrendingUp,
    children: [
      { path: '/analytics', label: 'Vue d\'ensemble', icon: BarChart3 },
    ],
  },
  {
    label: 'Paramètres',
    icon: Settings,
    children: [
      { path: '/settings/alerts', label: 'Alertes', icon: Bell },
    ],
  },
  {
    label: 'Administration',
    icon: Shield,
    children: [
      { path: '/admin/sources', label: 'Sources', icon: Server },
      { path: '/admin/organizations', label: 'Clients', icon: Building2 },
    ],
  },
]

function NavLink({ item, collapsed }: { item: NavChild; collapsed: boolean }) {
  const location = useLocation()
  const isActive = location.pathname === item.path
  const Icon = item.icon

  return (
    <Link
      to={item.path}
      className={cn(
        'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-sidebar-accent text-primary'
          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground',
        collapsed && 'justify-center px-2',
      )}
      title={collapsed ? item.label : undefined}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  )
}

function NavGroupItem({ group, collapsed }: { group: NavGroup; collapsed: boolean }) {
  const location = useLocation()
  const isChildActive = group.children.some((c) => location.pathname === c.path)
  const [open, setOpen] = useState(isChildActive)
  const Icon = group.icon

  if (collapsed) {
    // In collapsed mode, show only the first child link with the group icon
    const firstActive = group.children.find((c) => location.pathname === c.path)
    const target = firstActive || group.children[0]
    return (
      <Link
        to={target.path}
        className={cn(
          'flex items-center justify-center rounded-md px-2 py-2 text-sm font-medium transition-colors',
          isChildActive
            ? 'bg-sidebar-accent text-primary'
            : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground',
        )}
        title={group.label}
      >
        <Icon className="h-4 w-4 shrink-0" />
      </Link>
    )
  }

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
          isChildActive
            ? 'text-primary'
            : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground',
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span className="flex-1 text-left">{group.label}</span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 shrink-0 transition-transform duration-200',
            open && 'rotate-180',
          )}
        />
      </button>
      {open && (
        <div className="ml-4 mt-0.5 space-y-0.5 border-l border-sidebar-border pl-3">
          {group.children.map((child) => (
            <NavLink key={child.path} item={child} collapsed={false} />
          ))}
        </div>
      )}
    </div>
  )
}

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Logo */}
      <div className={cn(
        'flex h-14 items-center border-b border-sidebar-border px-4',
        collapsed && 'justify-center px-2',
      )}>
        <Link to="/" className="flex items-center gap-2.5 overflow-hidden">
          <Radar className="h-6 w-6 shrink-0 text-primary" />
          {!collapsed && (
            <span className="text-base font-bold tracking-tight text-sidebar-foreground whitespace-nowrap">
              MediaWatch <span className="text-primary">CI</span>
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-3">
        {navigation.map((item, idx) =>
          isGroup(item) ? (
            <NavGroupItem key={idx} group={item} collapsed={collapsed} />
          ) : (
            <NavLink key={item.path} item={item} collapsed={collapsed} />
          ),
        )}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-md p-2 text-sidebar-foreground/50 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
          title={collapsed ? 'Ouvrir le menu' : 'Réduire le menu'}
        >
          <svg
            className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </aside>
  )
}
