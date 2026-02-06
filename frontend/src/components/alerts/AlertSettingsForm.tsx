import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Loader2, Save, Bell, BellOff } from 'lucide-react'

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

interface AlertSettingsFormProps {
  settings: AlertSettings
  onSave: (data: Partial<AlertSettings>) => Promise<void>
  isSaving: boolean
}

const FREQUENCY_OPTIONS = [
  { value: 'immediate', label: 'Immédiat', description: 'Alerte envoyée dès détection' },
  { value: 'batch_1h', label: 'Toutes les heures', description: 'Résumé groupé chaque heure' },
  { value: 'batch_4h', label: 'Toutes les 4 heures', description: 'Résumé groupé toutes les 4h' },
  { value: 'daily', label: 'Quotidien', description: 'Résumé quotidien le matin' },
]

const CHANNEL_OPTIONS = [
  { value: 'email', label: 'Email', available: true },
  { value: 'sms', label: 'SMS', available: false },
  { value: 'whatsapp', label: 'WhatsApp', available: false },
]

export default function AlertSettingsForm({ settings, onSave, isSaving }: AlertSettingsFormProps) {
  const [enabled, setEnabled] = useState(settings.enabled)
  const [channel, setChannel] = useState(settings.channel)
  const [frequency, setFrequency] = useState(settings.frequency)
  const [negativeOnly, setNegativeOnly] = useState(settings.negative_only)
  const [minScore, setMinScore] = useState(settings.min_sentiment_score)
  const [quietStart, setQuietStart] = useState(settings.quiet_hours_start || '')
  const [quietEnd, setQuietEnd] = useState(settings.quiet_hours_end || '')
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    setEnabled(settings.enabled)
    setChannel(settings.channel)
    setFrequency(settings.frequency)
    setNegativeOnly(settings.negative_only)
    setMinScore(settings.min_sentiment_score)
    setQuietStart(settings.quiet_hours_start || '')
    setQuietEnd(settings.quiet_hours_end || '')
    setHasChanges(false)
  }, [settings])

  const markChanged = () => setHasChanges(true)

  const handleSave = async () => {
    await onSave({
      enabled,
      channel,
      frequency,
      negative_only: negativeOnly,
      min_sentiment_score: minScore,
      quiet_hours_start: quietStart || null,
      quiet_hours_end: quietEnd || null,
    })
    setHasChanges(false)
  }

  // T052 - Toggle activation/désactivation
  const handleToggle = async () => {
    const newEnabled = !enabled
    setEnabled(newEnabled)
    await onSave({ enabled: newEnabled })
  }

  return (
    <div className="space-y-6">
      {/* Toggle principal */}
      <Card>
        <CardContent className="flex items-center justify-between p-6">
          <div className="flex items-center gap-3">
            {enabled ? (
              <Bell className="h-5 w-5 text-primary" />
            ) : (
              <BellOff className="h-5 w-5 text-muted-foreground" />
            )}
            <div>
              <h3 className="font-medium">
                Alertes {enabled ? 'activées' : 'désactivées'}
              </h3>
              <p className="text-sm text-muted-foreground">
                {enabled
                  ? 'Vous recevrez des notifications selon vos paramètres'
                  : 'Aucune alerte ne sera envoyée'}
              </p>
            </div>
          </div>
          <Button
            variant={enabled ? 'destructive' : 'default'}
            size="sm"
            onClick={handleToggle}
            disabled={isSaving}
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : enabled ? (
              'Désactiver'
            ) : (
              'Activer'
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Paramètres détaillés */}
      {enabled && (
        <>
          {/* Canal */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Canal de notification</CardTitle>
              <CardDescription>Comment souhaitez-vous recevoir vos alertes ?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-3">
                {CHANNEL_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      channel === opt.value
                        ? 'border-primary bg-primary/5'
                        : opt.available
                        ? 'hover:border-primary/30'
                        : 'opacity-50 cursor-not-allowed'
                    }`}
                    onClick={() => {
                      if (opt.available) {
                        setChannel(opt.value)
                        markChanged()
                      }
                    }}
                    disabled={!opt.available}
                  >
                    <span className="font-medium">{opt.label}</span>
                    {!opt.available && (
                      <Badge variant="secondary" className="ml-2 text-xs">
                        Bientôt
                      </Badge>
                    )}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Fréquence */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Fréquence d'envoi</CardTitle>
              <CardDescription>À quelle fréquence recevoir les alertes ?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {FREQUENCY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      frequency === opt.value
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-primary/30'
                    }`}
                    onClick={() => {
                      setFrequency(opt.value)
                      markChanged()
                    }}
                  >
                    <span className="font-medium">{opt.label}</span>
                    <p className="mt-1 text-xs text-muted-foreground">{opt.description}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Filtres */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filtres</CardTitle>
              <CardDescription>Affiner les conditions de déclenchement</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Mentions négatives uniquement</Label>
                  <p className="text-xs text-muted-foreground">
                    Ne recevoir que les alertes pour les mentions à sentiment négatif
                  </p>
                </div>
                <button
                  className={`relative h-6 w-11 rounded-full transition-colors ${
                    negativeOnly ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => {
                    setNegativeOnly(!negativeOnly)
                    markChanged()
                  }}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                      negativeOnly ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              <div>
                <Label>Seuil de sentiment minimum</Label>
                <p className="mb-2 text-xs text-muted-foreground">
                  Score minimum pour déclencher une alerte (0 = tout, 1 = très négatif)
                </p>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={minScore}
                    onChange={(e) => {
                      setMinScore(parseFloat(e.target.value))
                      markChanged()
                    }}
                    className="flex-1"
                  />
                  <span className="w-12 text-center text-sm font-medium">
                    {(minScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Heures calmes */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Heures calmes</CardTitle>
              <CardDescription>Période pendant laquelle les alertes sont suspendues</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Label>Début</Label>
                  <Input
                    type="time"
                    value={quietStart}
                    onChange={(e) => {
                      setQuietStart(e.target.value)
                      markChanged()
                    }}
                  />
                </div>
                <span className="mt-6 text-muted-foreground">à</span>
                <div className="flex-1">
                  <Label>Fin</Label>
                  <Input
                    type="time"
                    value={quietEnd}
                    onChange={(e) => {
                      setQuietEnd(e.target.value)
                      markChanged()
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bouton sauvegarder */}
          {hasChanges && (
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving} className="gap-2">
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Enregistrer les modifications
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
