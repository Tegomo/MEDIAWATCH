import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { X, Save, Loader2 } from 'lucide-react'
import api from '@/services/api'

const PLAN_OPTIONS = [
  { value: 'basic', label: 'Basic', keywords: 10, users: 1 },
  { value: 'pro', label: 'Pro', keywords: 50, users: 5 },
  { value: 'enterprise', label: 'Enterprise', keywords: 999, users: 999 },
]

const STATUS_OPTIONS = [
  { value: 'trial', label: 'Essai' },
  { value: 'active', label: 'Actif' },
  { value: 'suspended', label: 'Suspendu' },
  { value: 'canceled', label: 'Annulé' },
]

interface OrgFormData {
  id?: string
  name: string
  subscription_plan: string
  subscription_status: string
  keyword_limit: number
  user_limit: number
}

interface OrganizationFormModalProps {
  mode: 'create' | 'edit'
  initialData?: OrgFormData | null
  onClose: () => void
  onSuccess: () => void
}

export default function OrganizationFormModal({ mode, initialData, onClose, onSuccess }: OrganizationFormModalProps) {
  const [name, setName] = useState('')
  const [plan, setPlan] = useState('basic')
  const [status, setStatus] = useState('trial')
  const [keywordLimit, setKeywordLimit] = useState(10)
  const [userLimit, setUserLimit] = useState(1)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      setName(initialData.name)
      setPlan(initialData.subscription_plan)
      setStatus(initialData.subscription_status)
      setKeywordLimit(initialData.keyword_limit)
      setUserLimit(initialData.user_limit)
    }
  }, [mode, initialData])

  const handlePlanChange = (newPlan: string) => {
    setPlan(newPlan)
    const preset = PLAN_OPTIONS.find((p) => p.value === newPlan)
    if (preset && mode === 'create') {
      setKeywordLimit(preset.keywords)
      setUserLimit(preset.users)
    }
  }

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Le nom est requis')
      return
    }
    setError(null)
    setSaving(true)

    try {
      if (mode === 'create') {
        await api.post('/admin/organizations', {
          name: name.trim(),
          subscription_plan: plan,
          subscription_status: status,
          keyword_limit: keywordLimit,
          user_limit: userLimit,
        })
      } else if (initialData?.id) {
        await api.put(`/admin/organizations/${initialData.id}`, {
          name: name.trim(),
          subscription_plan: plan,
          subscription_status: status,
          keyword_limit: keywordLimit,
          user_limit: userLimit,
        })
      }
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr?.response?.data?.detail || 'Une erreur est survenue')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="mx-4 w-full max-w-lg rounded-lg bg-background p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold">
            {mode === 'create' ? 'Nouvelle organisation' : `Modifier ${initialData?.name || ''}`}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          {/* Nom */}
          <div className="space-y-1.5">
            <Label>Nom de l'organisation</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Agence Médias CI"
            />
          </div>

          {/* Plan */}
          <div className="space-y-1.5">
            <Label>Plan d'abonnement</Label>
            <div className="flex gap-2">
              {PLAN_OPTIONS.map((p) => (
                <Button
                  key={p.value}
                  type="button"
                  variant={plan === p.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handlePlanChange(p.value)}
                  className="flex-1"
                >
                  {p.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Statut */}
          <div className="space-y-1.5">
            <Label>Statut</Label>
            <div className="flex gap-2">
              {STATUS_OPTIONS.map((s) => (
                <Button
                  key={s.value}
                  type="button"
                  variant={status === s.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatus(s.value)}
                  className="flex-1"
                >
                  {s.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Limites */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Limite mots-clés</Label>
              <Input
                type="number"
                min={1}
                value={keywordLimit}
                onChange={(e) => setKeywordLimit(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Limite utilisateurs</Label>
              <Input
                type="number"
                min={1}
                value={userLimit}
                onChange={(e) => setUserLimit(Number(e.target.value))}
              />
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={onClose}>
              Annuler
            </Button>
            <Button size="sm" onClick={handleSubmit} disabled={saving} className="gap-1">
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
              {mode === 'create' ? 'Créer' : 'Enregistrer'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
