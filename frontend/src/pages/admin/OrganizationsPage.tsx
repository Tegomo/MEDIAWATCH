import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, Building2, Users, Crown, Plus } from 'lucide-react'
import OrganizationTable from '@/components/admin/OrganizationTable'
import OrganizationDetailModal from '@/components/admin/OrganizationDetailModal'
import OrganizationFormModal from '@/components/admin/OrganizationFormModal'
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

interface OrgsResponse {
  organizations: OrgData[]
}

const PLAN_OPTIONS = ['basic', 'pro', 'enterprise']
const STATUS_OPTIONS = ['active', 'trial', 'suspended', 'canceled']

export default function OrganizationsPage() {
  const [planFilter, setPlanFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null)
  const [editingOrg, setEditingOrg] = useState<OrgData | null>(null)

  const { data, isLoading, refetch, isRefetching } = useQuery<OrgsResponse>({
    queryKey: ['admin-organizations', planFilter, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (planFilter) params.set('plan', planFilter)
      if (statusFilter) params.set('status', statusFilter)
      const resp = await api.get<OrgsResponse>(`/admin/organizations?${params}`)
      return resp.data
    },
    refetchInterval: 30 * 1000,
  })

  const orgs = data?.organizations || []
  const activeCount = orgs.filter((o) => o.subscription_status === 'active').length
  const suspendedCount = orgs.filter((o) => o.subscription_status === 'suspended').length
  const trialCount = orgs.filter((o) => o.subscription_status === 'trial').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Building2 className="h-6 w-6" />
            Gestion des Organisations
          </h1>
          <p className="text-muted-foreground">
            Gérer les comptes clients, limites et abonnements
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => { setFormMode('create'); setEditingOrg(null) }}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Nouvelle organisation
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{orgs.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Actives</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{activeCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Essai</CardTitle>
            <Crown className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{trialCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Suspendues</CardTitle>
            <Building2 className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{suspendedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* T119 - Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs font-medium text-muted-foreground">Plan:</span>
        {PLAN_OPTIONS.map((p) => (
          <Badge
            key={p}
            variant={planFilter === p ? 'default' : 'outline'}
            className="cursor-pointer text-xs"
            onClick={() => setPlanFilter(planFilter === p ? null : p)}
          >
            {p.toUpperCase()}
          </Badge>
        ))}
        <div className="h-4 w-px bg-border" />
        <span className="text-xs font-medium text-muted-foreground">Statut:</span>
        {STATUS_OPTIONS.map((s) => (
          <Badge
            key={s}
            variant={statusFilter === s ? 'default' : 'outline'}
            className="cursor-pointer text-xs"
            onClick={() => setStatusFilter(statusFilter === s ? null : s)}
          >
            {s}
          </Badge>
        ))}
        {(planFilter || statusFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setPlanFilter(null); setStatusFilter(null) }}
            className="h-6 text-xs"
          >
            Effacer
          </Button>
        )}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : (
        <OrganizationTable
          organizations={orgs}
          onRefresh={() => refetch()}
          onViewDetail={setSelectedOrgId}
          onEdit={(org) => { setEditingOrg(org); setFormMode('edit') }}
          onDelete={async (orgId, orgName) => {
            if (!confirm(`Supprimer l'organisation "${orgName}" et toutes ses données ? Cette action est irréversible.`)) return
            try {
              await api.delete(`/admin/organizations/${orgId}`)
              refetch()
            } catch { /* */ }
          }}
        />
      )}

      {/* Detail modal */}
      {selectedOrgId && (
        <OrganizationDetailModal
          orgId={selectedOrgId}
          onClose={() => setSelectedOrgId(null)}
          onRefresh={() => refetch()}
        />
      )}

      {/* Create / Edit modal */}
      {formMode && (
        <OrganizationFormModal
          mode={formMode}
          initialData={editingOrg}
          onClose={() => { setFormMode(null); setEditingOrg(null) }}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  )
}
