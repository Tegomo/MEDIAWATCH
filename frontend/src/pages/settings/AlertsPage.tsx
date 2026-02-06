import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Bell } from 'lucide-react'
import AlertSettingsForm from '@/components/alerts/AlertSettingsForm'
import api from '@/services/api'

interface AlertSettings {
  id: string
  user_id: string
  enabled: boolean
  channel: string
  frequency: string
  negative_only: boolean
  min_sentiment_score: number
  quiet_hours_start: string | null
  quiet_hours_end: string | null
}

export default function AlertsPage() {
  const queryClient = useQueryClient()
  const [saveError, setSaveError] = useState<string | null>(null)

  const { data: settings, isLoading } = useQuery<AlertSettings>({
    queryKey: ['alert-settings'],
    queryFn: async () => {
      const response = await api.get<AlertSettings>('/alerts/settings')
      return response.data
    },
  })

  const mutation = useMutation({
    mutationFn: async (data: Partial<AlertSettings>) => {
      const response = await api.patch<AlertSettings>('/alerts/settings', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-settings'] })
      setSaveError(null)
    },
    onError: () => {
      setSaveError('Erreur lors de la sauvegarde des paramètres')
    },
  })

  const handleSave = async (data: Partial<AlertSettings>) => {
    await mutation.mutateAsync(data)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Bell className="h-6 w-6" />
          Paramètres des alertes
        </h1>
        <p className="text-muted-foreground">
          Configurez comment et quand vous souhaitez recevoir les alertes de mentions
        </p>
      </div>

      {saveError && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {saveError}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : settings ? (
        <AlertSettingsForm
          settings={settings}
          onSave={handleSave}
          isSaving={mutation.isPending}
        />
      ) : (
        <div className="text-center text-muted-foreground py-12">
          Impossible de charger les paramètres d'alertes
        </div>
      )}
    </div>
  )
}
