import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { X, Save, Loader2 } from 'lucide-react'
import api from '@/services/api'

interface OrgDetail {
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
  users: Array<{
    id: string
    email: string
    full_name: string
    role: string
    created_at: string
  }>
}

interface OrganizationDetailModalProps {
  orgId: string | null
  onClose: () => void
  onRefresh: () => void
}

export default function OrganizationDetailModal({ orgId, onClose, onRefresh }: OrganizationDetailModalProps) {
  const [keywordLimit, setKeywordLimit] = useState(0)
  const [userLimit, setUserLimit] = useState(0)
  const [saving, setSaving] = useState(false)

  const { data: org } = useQuery<OrgDetail>({
    queryKey: ['admin-org-detail', orgId],
    queryFn: async () => {
      const resp = await api.get<OrgDetail>(`/admin/organizations/${orgId}`)
      return resp.data
    },
    enabled: !!orgId,
  })

  useEffect(() => {
    if (org) {
      setKeywordLimit(org.keyword_limit)
      setUserLimit(org.user_limit)
    }
  }, [org])

  const handleSaveLimits = async () => {
    if (!orgId) return
    setSaving(true)
    try {
      await api.patch(`/admin/organizations/${orgId}/limits`, {
        keyword_limit: keywordLimit,
        user_limit: userLimit,
      })
      onRefresh()
    } catch { /* */ } finally {
      setSaving(false)
    }
  }

  if (!orgId) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="mx-4 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-background p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">{org?.name || 'Chargement...'}</h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {org && (
          <div className="space-y-5">
            {/* Info */}
            <div className="flex gap-2">
              <Badge variant="outline" className="text-xs">
                {org.subscription_plan.toUpperCase()}
              </Badge>
              <Badge
                variant="outline"
                className={`text-xs ${
                  org.subscription_status === 'active' ? 'bg-green-100 text-green-700' :
                  org.subscription_status === 'suspended' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-600'
                }`}
              >
                {org.subscription_status}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Créé le {new Date(org.created_at).toLocaleDateString('fr-FR')}
              </span>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-xl font-bold">{org.user_count}/{org.user_limit}</div>
                  <div className="text-xs text-muted-foreground">Utilisateurs</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-xl font-bold">{org.keyword_count}/{org.keyword_limit}</div>
                  <div className="text-xs text-muted-foreground">Mots-clés</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-xl font-bold">{org.mention_count}</div>
                  <div className="text-xs text-muted-foreground">Mentions</div>
                </CardContent>
              </Card>
            </div>

            {/* Limits */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Limites</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Limite mots-clés</Label>
                    <Input
                      type="number"
                      value={keywordLimit}
                      onChange={(e) => setKeywordLimit(Number(e.target.value))}
                      className="h-8"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Limite utilisateurs</Label>
                    <Input
                      type="number"
                      value={userLimit}
                      onChange={(e) => setUserLimit(Number(e.target.value))}
                      className="h-8"
                    />
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={handleSaveLimits}
                  disabled={saving || (keywordLimit === org.keyword_limit && userLimit === org.user_limit)}
                  className="gap-1"
                >
                  {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                  Enregistrer
                </Button>
              </CardContent>
            </Card>

            {/* Users */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Utilisateurs ({org.users.length})</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="px-4 py-2 text-left text-xs font-medium">Email</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Nom</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Rôle</th>
                      <th className="px-4 py-2 text-left text-xs font-medium">Inscrit le</th>
                    </tr>
                  </thead>
                  <tbody>
                    {org.users.map((user) => (
                      <tr key={user.id} className="border-b last:border-0">
                        <td className="px-4 py-2 text-xs">{user.email}</td>
                        <td className="px-4 py-2 text-xs">{user.full_name || '—'}</td>
                        <td className="px-4 py-2">
                          <Badge variant="outline" className="text-[10px]">{user.role}</Badge>
                        </td>
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {new Date(user.created_at).toLocaleDateString('fr-FR')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
