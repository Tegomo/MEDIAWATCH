import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, TrendingUp, TrendingDown, Minus, RefreshCw, Search, Inbox } from 'lucide-react'
import MentionList from '@/components/mentions/MentionList'
import MentionDetailModal from '@/components/mentions/MentionDetailModal'
import FilterBar, { EMPTY_FILTERS, hasActiveFilters } from '@/components/filters/FilterBar'
import type { Filters } from '@/components/filters/FilterBar'
import ExportButton from '@/components/exports/ExportButton'
import ScanDialog from '@/components/scan/ScanDialog'
import api from '@/services/api'

interface MentionListResponse {
  mentions: Array<{
    id: string
    matched_text: string
    match_context: string
    sentiment_score: number
    sentiment_label: string
    visibility_score: number
    theme: string | null
    detected_at: string
    keyword: { id: string; text: string; category: string } | null
    article: {
      id: string
      title: string
      url: string
      author: string | null
      published_at: string
      source: { id: string; name: string; url: string; type: string } | null
    } | null
  }>
  total: number
  limit: number
  offset: number
}

interface MentionStats {
  total_mentions: number
  by_sentiment: Record<string, number>
}

export default function DashboardPage() {
  const [offset, setOffset] = useState(0)
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState<Filters>(EMPTY_FILTERS)
  const [selectedMentionId, setSelectedMentionId] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState('')
  const [scanResult, setScanResult] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const limit = 20

  const handleScan = async (params: { keyword_id?: string; date_from?: string; date_to?: string } = {}) => {
    setScanning(true)
    setScanResult(null)
    setScanProgress('Démarrage…')
    try {
      const launch = await api.post<{ success: boolean; message: string }>('/mentions/scan', params)
      if (!launch.data.success) {
        setScanResult(launch.data.message)
        setScanning(false)
        return
      }

      const poll = async (): Promise<void> => {
        const s = await api.get<{
          running: boolean
          progress: string
          result: {
            success: boolean
            message: string
            details?: {
              sources_scannees: number
              liens_articles: number
              nouveaux_articles_sources?: number
              nouveaux_articles_recherche?: number
              nouveaux_articles_total?: number
              nouveaux_articles?: number
              articles_analyses: number
              mentions_creees: number
              erreurs_scraping: string[]
              erreurs_nlp: number
            }
          } | null
        }>('/mentions/scan/status')

        if (s.data.running) {
          setScanProgress(s.data.progress || 'En cours…')
          await new Promise(r => setTimeout(r, 3000))
          return poll()
        }

        const r = s.data.result
        if (r?.details) {
          const d = r.details
          const totalArticles = d.nouveaux_articles_total ?? d.nouveaux_articles ?? 0
          const fromSources = d.nouveaux_articles_sources ?? totalArticles
          const fromSearch = d.nouveaux_articles_recherche ?? 0
          const parts = [
            `${d.sources_scannees} sources scannées`,
            `${d.liens_articles} liens découverts`,
            `${fromSources} articles (sources)`,
            `${fromSearch} articles (recherche web)`,
            `${d.mentions_creees} mentions créées`,
          ]
          let msg = parts.join(' · ')
          if (d.erreurs_scraping?.length) {
            msg += '\n⚠️ ' + d.erreurs_scraping.join('\n⚠️ ')
          }
          setScanResult(msg)
        } else {
          setScanResult(r?.message || 'Scan terminé')
        }
        setScanning(false)
        setScanProgress('')
        queryClient.invalidateQueries({ queryKey: ['mentions'] })
        queryClient.invalidateQueries({ queryKey: ['mention-stats'] })
      }

      await poll()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setScanResult(axiosErr?.response?.data?.detail || 'Erreur lors du scan')
      setScanning(false)
      setScanProgress('')
    }
  }

  const applyFilters = () => {
    setAppliedFilters({ ...filters })
    setOffset(0)
  }

  // Auto-apply on sentiment/theme/date change, defer search to Enter key
  const handleFiltersChange = useCallback((newFilters: Filters) => {
    setFilters(newFilters)
    setAppliedFilters((prev) => {
      // If only the search text changed, don't auto-apply (wait for Enter)
      if (
        newFilters.sentiment === prev.sentiment &&
        newFilters.theme === prev.theme &&
        newFilters.dateFrom === prev.dateFrom &&
        newFilters.dateTo === prev.dateTo
      ) {
        return prev
      }
      // A non-search filter changed → apply immediately
      setOffset(0)
      return { ...newFilters }
    })
  }, [])

  const handleClear = () => {
    setFilters(EMPTY_FILTERS)
    setAppliedFilters(EMPTY_FILTERS)
    setOffset(0)
  }

  // Auto-refresh toutes les 5 minutes
  const { data, isLoading, isRefetching, refetch } = useQuery<MentionListResponse>({
    queryKey: ['mentions', offset, appliedFilters],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.set('limit', String(limit))
      params.set('offset', String(offset))
      if (appliedFilters.sentiment) params.set('sentiment', appliedFilters.sentiment)
      if (appliedFilters.search) params.set('search', appliedFilters.search)
      if (appliedFilters.theme) params.set('theme', appliedFilters.theme)
      if (appliedFilters.dateFrom) params.set('date_from', `${appliedFilters.dateFrom}T00:00:00`)
      if (appliedFilters.dateTo) params.set('date_to', `${appliedFilters.dateTo}T23:59:59`)
      const response = await api.get<MentionListResponse>(`/mentions?${params}`)
      return response.data
    },
    refetchInterval: 5 * 60 * 1000,
  })

  const { data: stats } = useQuery<MentionStats>({
    queryKey: ['mention-stats'],
    queryFn: async () => {
      const response = await api.get<MentionStats>('/mentions/stats')
      return response.data
    },
    refetchInterval: 5 * 60 * 1000,
  })

  const handlePageChange = useCallback((newOffset: number) => {
    setOffset(newOffset)
  }, [])

  const positiveCount = stats?.by_sentiment?.POSITIVE || stats?.by_sentiment?.positive || 0
  const negativeCount = stats?.by_sentiment?.NEGATIVE || stats?.by_sentiment?.negative || 0
  const neutralCount = stats?.by_sentiment?.NEUTRAL || stats?.by_sentiment?.neutral || 0
  const filtersActive = hasActiveFilters(appliedFilters)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Mentions récentes dans les médias ivoiriens</p>
        </div>
        <div className="flex items-center gap-2">
          <ScanDialog scanning={scanning} onScanStart={handleScan} />
          <ExportButton filters={appliedFilters} />
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

      {/* Progression du scan */}
      {scanning && scanProgress && (
        <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm text-primary">
          ⏳ {scanProgress}
        </div>
      )}

      {/* Résultat du scan */}
      {scanResult && (
        <div className="flex items-center justify-between rounded-lg border bg-muted/50 px-4 py-2.5 text-sm">
          <span className="whitespace-pre-line">{scanResult}</span>
          <button
            onClick={() => setScanResult(null)}
            className="ml-4 shrink-0 text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>
      )}

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total mentions</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_mentions || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Positives</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{positiveCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Neutres</CardTitle>
            <Minus className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{neutralCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Négatives</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{negativeCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <FilterBar
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onSearch={applyFilters}
        onClear={handleClear}
      />

      {/* Mentions list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : data && data.mentions.length > 0 ? (
        <MentionList
          mentions={data.mentions}
          total={data.total}
          limit={data.limit}
          offset={data.offset}
          onPageChange={handlePageChange}
          onMentionClick={setSelectedMentionId}
        />
      ) : (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Inbox className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium">
              {filtersActive ? 'Aucun résultat' : 'Aucune mention récente'}
            </h3>
            <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
              {filtersActive
                ? 'Aucune mention ne correspond à vos filtres. Essayez d\'ajuster vos critères de recherche ou de réduire les filtres appliqués.'
                : 'Les mentions apparaîtront ici dès que vos mots-clés seront détectés dans les médias. Assurez-vous d\'avoir configuré vos mots-clés.'}
            </p>
            {filtersActive && (
              <Button variant="outline" className="mt-4" onClick={handleClear}>
                Effacer tous les filtres
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modal détail */}
      <MentionDetailModal
        mentionId={selectedMentionId}
        onClose={() => setSelectedMentionId(null)}
      />
    </div>
  )
}
