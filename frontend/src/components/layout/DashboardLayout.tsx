import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { LogOut, User, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { signOut } from '@/services/supabase'
import Sidebar from './Sidebar'
import { cn } from '@/lib/utils'
import { useTheme } from '@/lib/useTheme'

export default function DashboardLayout() {
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const { theme, toggleTheme } = useTheme()

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Main area */}
      <div
        className={cn(
          'flex min-h-screen flex-col transition-all duration-300',
          collapsed ? 'ml-16' : 'ml-60',
        )}
      >
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-14 items-center justify-end gap-3 border-b border-border bg-background/80 px-6 backdrop-blur">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <div className="h-5 w-px bg-border" />
            <div className="flex items-center gap-2 rounded-md bg-muted px-3 py-1.5 text-sm text-muted-foreground">
              <User className="h-3.5 w-3.5" />
              <span>Admin</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="gap-2 text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              Déconnexion
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
