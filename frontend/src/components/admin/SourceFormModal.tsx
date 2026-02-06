import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { X, Save, Loader2 } from 'lucide-react'
import api from '@/services/api'

const TYPE_OPTIONS = [
  { value: 'press', label: 'Presse' },
  { value: 'rss', label: 'RSS' },
  { value: 'api', label: 'API' },
  { value: 'whatsapp', label: 'WhatsApp' },
]

interface SourceFormData {
  id?: string
  name: string
  url: string
  type: string
  scraper_class: string
  prestige_score: number
  scraping_enabled: boolean
}

interface SourceFormModalProps {
  mode: 'create' | 'edit'
  initialData?: SourceFormData | null
  onClose: () => void
  onSuccess: () => void
}

export default function SourceFormModal({ mode, initialData, onClose, onSuccess }: SourceFormModalProps) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [sourceType, setSourceType] = useState('press')
  const [scraperClass, setScraperClass] = useState('generic')
  const [prestigeScore, setPrestigeScore] = useState(0.5)
  const [scrapingEnabled, setScrapingEnabled] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      setName(initialData.name)
      setUrl(initialData.url)
      setSourceType(initialData.type)
      setScraperClass(initialData.scraper_class)
      setPrestigeScore(initialData.prestige_score)
      setScrapingEnabled(initialData.scraping_enabled)
    }
  }, [mode, initialData])

  const handleSubmit = async () => {
    if (!name.trim()) { setError('Le nom est requis'); return }
    if (!url.trim()) { setError("L'URL est requise"); return }
    setError(null)
    setSaving(true)

    const payload = {
      name: name.trim(),
      url: url.trim(),
      source_type: sourceType,
      scraper_class: scraperClass.trim(),
      prestige_score: prestigeScore,
      scraping_enabled: scrapingEnabled,
    }

    try {
      if (mode === 'create') {
        await api.post('/admin/sources', payload)
      } else if (initialData?.id) {
        await api.put(`/admin/sources/${initialData.id}`, payload)
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
            {mode === 'create' ? 'Nouvelle source' : `Modifier ${initialData?.name || ''}`}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          {/* Nom */}
          <div className="space-y-1.5">
            <Label>Nom de la source</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Fraternité Matin"
            />
          </div>

          {/* URL */}
          <div className="space-y-1.5">
            <Label>URL</Label>
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.example.com"
            />
          </div>

          {/* Type */}
          <div className="space-y-1.5">
            <Label>Type de source</Label>
            <div className="flex gap-2">
              {TYPE_OPTIONS.map((t) => (
                <Button
                  key={t.value}
                  type="button"
                  variant={sourceType === t.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSourceType(t.value)}
                  className="flex-1"
                >
                  {t.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Scraper class */}
          <div className="space-y-1.5">
            <Label>Classe scraper</Label>
            <Input
              value={scraperClass}
              onChange={(e) => setScraperClass(e.target.value)}
              placeholder="generic"
            />
            <p className="text-xs text-muted-foreground">
              Identifiant du scraper à utiliser (ex: fraternite_matin, abidjan_net, generic)
            </p>
          </div>

          {/* Prestige + Enabled */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Score de prestige (0-1)</Label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={prestigeScore}
                onChange={(e) => setPrestigeScore(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Scraping actif</Label>
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  role="switch"
                  aria-checked={scrapingEnabled}
                  onClick={() => setScrapingEnabled(!scrapingEnabled)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    scrapingEnabled ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${
                      scrapingEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className="text-sm">{scrapingEnabled ? 'Activé' : 'Désactivé'}</span>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && <p className="text-sm text-red-600">{error}</p>}

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
