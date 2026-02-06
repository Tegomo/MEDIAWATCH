import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2, Eye, Ban, CheckCircle, Pencil, Trash2 } from 'lucide-react'
import api from '@/services/api'

interface OrgData {
  id: string
  name: string
  subscription_plan: string
  subscription_status: string
  keyword_limit: number
  user_limit: number
  user_count: number
  keyword_count: number
  mention_count: number
  created_at: string
}

interface OrganizationTableProps {
  organizations: OrgData[]
  onRefresh: () => void
  onViewDetail: (orgId: string) => void
  onEdit: (org: OrgData) => void
  onDelete: (orgId: string, orgName: string) => void
}

const PLAN_COLORS: Record<string, string> = {
  basic: 'bg-gray-100 text-gray-700',
  pro: 'bg-blue-100 text-blue-700',
  enterprise: 'bg-purple-100 text-purple-700',
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  trial: 'bg-yellow-100 text-yellow-700',
  suspended: 'bg-red-100 text-red-700',
  canceled: 'bg-gray-100 text-gray-500',
}

export default function OrganizationTable({ organizations, onRefresh, onViewDetail, onEdit, onDelete }: OrganizationTableProps) {
  const [actionId, setActionId] = useState<string | null>(null)

  const handleSuspend = async (orgId: string) => {
    if (!confirm('Voulez-vous vraiment suspendre cette organisation ?')) return
    setActionId(orgId)
    try {
      await api.post(`/admin/organizations/${orgId}/suspend`)
      onRefresh()
    } catch { /* */ } finally {
      setActionId(null)
    }
  }

  const handleReactivate = async (orgId: string) => {
    setActionId(orgId)
    try {
      await api.post(`/admin/organizations/${orgId}/reactivate`)
      onRefresh()
    } catch { /* */ } finally {
      setActionId(null)
    }
  }

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Organisation</th>
                <th className="px-4 py-3 text-left font-medium">Plan</th>
                <th className="px-4 py-3 text-left font-medium">Statut</th>
                <th className="px-4 py-3 text-center font-medium">Users</th>
                <th className="px-4 py-3 text-center font-medium">Keywords</th>
                <th className="px-4 py-3 text-center font-medium">Mentions</th>
                <th className="px-4 py-3 text-left font-medium">Créé le</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {organizations.map((org) => (
                <tr key={org.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{org.name}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className={`text-xs ${PLAN_COLORS[org.subscription_plan] || ''}`}>
                      {org.subscription_plan.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className={`text-xs ${STATUS_COLORS[org.subscription_status] || ''}`}>
                      {org.subscription_status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-muted-foreground">{org.user_count}</span>
                    <span className="text-xs text-muted-foreground">/{org.user_limit}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-muted-foreground">{org.keyword_count}</span>
                    <span className="text-xs text-muted-foreground">/{org.keyword_limit}</span>
                  </td>
                  <td className="px-4 py-3 text-center text-muted-foreground">
                    {org.mention_count}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatDate(org.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(org.id)}
                        className="h-7 w-7 p-0"
                        title="Voir détails"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(org)}
                        className="h-7 w-7 p-0"
                        title="Modifier"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      {org.subscription_status === 'suspended' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReactivate(org.id)}
                          disabled={actionId === org.id}
                          className="h-7 gap-1 text-xs text-green-600"
                        >
                          {actionId === org.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3" />}
                          Réactiver
                        </Button>
                      ) : org.subscription_status !== 'canceled' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSuspend(org.id)}
                          disabled={actionId === org.id}
                          className="h-7 gap-1 text-xs text-red-600"
                        >
                          {actionId === org.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Ban className="h-3 w-3" />}
                          Suspendre
                        </Button>
                      ) : null}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(org.id, org.name)}
                        className="h-7 w-7 p-0 text-red-500 hover:text-red-700"
                        title="Supprimer"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
