import { useState, useEffect, useRef } from 'react'
import { Radar, Loader2, ChevronDown, X, Globe } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import api from '@/services/api'
import { useQueryClient } from '@tanstack/react-query'

interface Keyword {
  id: string
  text: string
  category: string
  enabled: boolean
}

interface ScanDialogProps {
  scanning: boolean
  onScanStart: (params: { keyword_id?: string; date_from?: string; date_to?: string }) => void
}

export default function ScanDialog({ scanning, onScanStart }: ScanDialogProps) {
  const [open, setOpen] = useState(false)
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [selectedKeywordId, setSelectedKeywordId] = useState<string>('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [loadingKw, setLoadingKw] = useState(false)
  const [scanUrl, setScanUrl] = useState('')
  const [scanUrlLoading, setScanUrlLoading] = useState(false)
  const [scanUrlResult, setScanUrlResult] = useState<string | null>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (open && keywords.length === 0) {
      setLoadingKw(true)
      api.get<{ keywords: Keyword[] }>('/keywords')
        .then((res) => {
          const list = res.data?.keywords ?? []
          const active = list.filter((k) => k.enabled)
          setKeywords(active)
        })
        .catch(() => setKeywords([]))
        .finally(() => setLoadingKw(false))
    }
  }, [open, keywords.length])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const handleLaunch = () => {
    const params: { keyword_id?: string; date_from?: string; date_to?: string } = {}
    if (selectedKeywordId) params.keyword_id = selectedKeywordId
    if (dateFrom) params.date_from = `${dateFrom}T00:00:00`
    if (dateTo) params.date_to = `${dateTo}T23:59:59`
    onScanStart(params)
    setOpen(false)
  }

  const handleScanAll = () => {
    onScanStart({})
  }

  const handleScanUrl = async () => {
    if (!scanUrl.trim()) return
    setScanUrlLoading(true)
    setScanUrlResult(null)
    try {
      const res = await api.post<{ success: boolean; message: string; mentions_created: number }>('/mentions/scan/url', { url: scanUrl.trim() })
      setScanUrlResult(res.data.message)
      setScanUrl('')
      queryClient.invalidateQueries({ queryKey: ['mentions'] })
      queryClient.invalidateQueries({ queryKey: ['mention-stats'] })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setScanUrlResult(axiosErr?.response?.data?.detail || 'Erreur lors du scan URL')
    } finally {
      setScanUrlLoading(false)
    }
  }

  const hasParams = selectedKeywordId || dateFrom || dateTo
  const selectedKw = keywords.find((k) => k.id === selectedKeywordId)

  return (
    <div className="relative" ref={panelRef}>
      <div className="flex items-center gap-1">
        <Button
          size="sm"
          onClick={handleScanAll}
          disabled={scanning}
          className="gap-2 rounded-r-none"
        >
          {scanning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Radar className="h-4 w-4" />
          )}
          {scanning ? 'Scan en cours…' : 'Lancer un scan'}
        </Button>
        <Button
          size="sm"
          onClick={() => setOpen(!open)}
          disabled={scanning}
          className="rounded-l-none border-l border-primary-foreground/20 px-2"
        >
          <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
        </Button>
      </div>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-popover p-4 shadow-lg">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="text-sm font-semibold">Scan avancé</h4>
            <button onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Mot-clé</Label>
              {loadingKw ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" /> Chargement…
                </div>
              ) : (
                <select
                  value={selectedKeywordId}
                  onChange={(e) => setSelectedKeywordId(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">Tous les mots-clés</option>
                  {keywords.map((kw) => (
                    <option key={kw.id} value={kw.id}>
                      {kw.text} ({kw.category})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1.5">
                <Label className="text-xs">Date début</Label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Date fin</Label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>
            </div>

            {hasParams && (
              <div className="rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Résumé :</span>{' '}
                {selectedKw ? `"${selectedKw.text}"` : 'Tous les mots-clés'}
                {dateFrom && ` · du ${dateFrom}`}
                {dateTo && ` · au ${dateTo}`}
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <Button
                size="sm"
                className="flex-1 gap-2"
                onClick={handleLaunch}
                disabled={scanning}
              >
                <Radar className="h-3.5 w-3.5" />
                {hasParams ? 'Scan ciblé' : 'Scan complet'}
              </Button>
              {hasParams && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setSelectedKeywordId('')
                    setDateFrom('')
                    setDateTo('')
                  }}
                >
                  Réinitialiser
                </Button>
              )}
            </div>

            <div className="border-t pt-3 mt-1">
              <div className="space-y-1.5">
                <Label className="flex items-center gap-1.5 text-xs">
                  <Globe className="h-3 w-3" />
                  Scanner une URL
                </Label>
                <div className="flex gap-1.5">
                  <Input
                    type="url"
                    placeholder="https://example.com/article..."
                    value={scanUrl}
                    onChange={(e) => { setScanUrl(e.target.value); setScanUrlResult(null) }}
                    className="h-9 text-xs flex-1"
                    onKeyDown={(e) => e.key === 'Enter' && handleScanUrl()}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleScanUrl}
                    disabled={scanUrlLoading || !scanUrl.trim()}
                    className="h-9 gap-1.5 px-3"
                  >
                    {scanUrlLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Globe className="h-3 w-3" />}
                    Scan
                  </Button>
                </div>
                {scanUrlResult && (
                  <p className="text-xs text-muted-foreground bg-muted/50 rounded-md p-2 mt-1">
                    {scanUrlResult}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
