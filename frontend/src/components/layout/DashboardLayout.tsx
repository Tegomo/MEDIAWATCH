import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { BarChart3, Bell, LogOut, Search, TrendingUp, Server, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { signOut } from '@/services/supabase'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { path: '/keywords', label: 'Mots-clés', icon: Search },
  { path: '/analytics', label: 'Analyses', icon: TrendingUp },
  { path: '/settings/alerts', label: 'Alertes', icon: Bell },
  { path: '/admin/sources', label: 'Sources', icon: Server },
  { path: '/admin/organizations', label: 'Clients', icon: Building2 },
]

export default function DashboardLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <span className="text-xl font-bold text-primary">MediaWatch CI</span>
          </Link>

          <nav className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive ? 'secondary' : 'ghost'}
                    size="sm"
                    className="gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Button>
                </Link>
              )
            })}
          </nav>

          <div className="ml-auto">
            <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              Déconnexion
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-6">
        <Outlet />
      </main>
    </div>
  )
}
