import { Badge } from '@/components/ui/badge'
import { CheckCircle, AlertTriangle, XCircle, Ban } from 'lucide-react'

interface SourceStatusBadgeProps {
  status: 'ok' | 'warning' | 'error' | 'disabled'
}

const STATUS_CONFIG = {
  ok: {
    label: 'OK',
    icon: CheckCircle,
    className: 'bg-green-100 text-green-700 border-green-300',
  },
  warning: {
    label: 'Instable',
    icon: AlertTriangle,
    className: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  },
  error: {
    label: 'Erreur',
    icon: XCircle,
    className: 'bg-red-100 text-red-700 border-red-300',
  },
  disabled: {
    label: 'Désactivé',
    icon: Ban,
    className: 'bg-gray-100 text-gray-500 border-gray-300',
  },
}

export default function SourceStatusBadge({ status }: SourceStatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.disabled
  const Icon = config.icon

  return (
    <Badge variant="outline" className={`gap-1 text-xs ${config.className}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
