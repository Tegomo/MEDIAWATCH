import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, Minus, BarChart3, Play, Loader2 } from 'lucide-react'
import TrendChart from '@/components/analytics/TrendChart'
import SourceChart from '@/components/analytics/SourceChart'
import api from '@/services/api'

interface TrendResponse {
  period_days: number
  total_mentions: number
  total_positive: number
  total_negative: number
  total_neutral: number
  trend: Array<{
    date: string
    total: number
    positive: number
    negative: number
    neutral: number
  }>
}

interface SourceResponse {
  period_days: number
  sources: Array<{
    name: string
    type: string
    mention_count: number
    avg_sentiment: number
  }>
  total_sources: number
}

interface TopKeywordsResponse {
  period_days: number
  keywords: Array<{
    text: string
    category: string
    mention_count: number
    avg_sentiment: number
  }>
}

export default function AnalyticsPage() {
  const [trendDays, setTrendDays] = useState(7)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState('')
  const [scanResult, setScanResult] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const handleScan = async () => {
    setScanning(true)
    setScanResult(null)
    setScanProgress('Démarrage…')
    try {
      const launch = await api.post<{ success: boolean; message: string }>('/mentions/scan')
      if (!launch.data.success) {
        setScanResult(launch.data.message)
        setScanning(false)
        return
      }

      // Poll /scan/status toutes les 3s
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

        // Scan terminé
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
        queryClient.invalidateQueries({ queryKey: ['analytics-trends'] })
        queryClient.invalidateQueries({ queryKey: ['analytics-sources'] })
        queryClient.invalidateQueries({ queryKey: ['analytics-keywords'] })
      }

      await poll()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setScanResult(axiosErr?.response?.data?.detail || 'Erreur lors du scan')
      setScanning(false)
    }
  }

  const { data: trends, isLoading: trendsLoading } = useQuery<TrendResponse>({
    queryKey: ['analytics-trends', trendDays],
    queryFn: async () => {
      const resp = await api.get<TrendResponse>(`/analytics/trends?days=${trendDays}`)
      return resp.data
    },
  })

  const { data: sources, isLoading: sourcesLoading } = useQuery<SourceResponse>({
    queryKey: ['analytics-sources'],
    queryFn: async () => {
      const resp = await api.get<SourceResponse>('/analytics/sources?days=30')
      return resp.data
    },
  })

  const { data: topKeywords } = useQuery<TopKeywordsResponse>({
    queryKey: ['analytics-keywords'],
    queryFn: async () => {
      const resp = await api.get<TopKeywordsResponse>('/analytics/keywords?days=30')
      return resp.data
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <BarChart3 className="h-6 w-6" />
            Analyses et Tendances
          </h1>
          <p className="text-muted-foreground">
            Visualisez l'évolution des mentions et la répartition par sources
          </p>
        </div>
        <Button onClick={handleScan} disabled={scanning} className="gap-2">
          {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {scanning ? 'Analyse en cours…' : 'Lancer l\'analyse'}
        </Button>
      </div>

      {scanning && scanProgress && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
          ⏳ {scanProgress}
        </div>
      )}

      {scanResult && (
        <div className="whitespace-pre-line rounded-md border bg-muted/50 p-3 text-sm">
          {scanResult}
        </div>
      )}

      {/* Summary cards */}
      {trends && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total ({trendDays}j)</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{trends.total_mentions}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Positives</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{trends.total_positive}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Neutres</CardTitle>
              <Minus className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">{trends.total_neutral}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Négatives</CardTitle>
              <TrendingDown className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{trends.total_negative}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trend chart */}
      <TrendChart
        data={trends?.trend || []}
        periodDays={trendDays}
        onPeriodChange={setTrendDays}
        isLoading={trendsLoading}
      />

      {/* Bottom row: Sources + Top Keywords */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Source distribution */}
        <SourceChart data={sources?.sources || []} isLoading={sourcesLoading} />

        {/* Top keywords */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">Top mots-clés (30j)</CardTitle>
          </CardHeader>
          <CardContent>
            {topKeywords && topKeywords.keywords.length > 0 ? (
              <div className="space-y-3">
                {topKeywords.keywords.map((kw, i) => {
                  const maxCount = topKeywords.keywords[0]?.mention_count || 1
                  const pct = (kw.mention_count / maxCount) * 100
                  const sentimentColor =
                    kw.avg_sentiment > 0.1
                      ? 'bg-green-500'
                      : kw.avg_sentiment < -0.1
                      ? 'bg-red-500'
                      : 'bg-gray-400'

                  return (
                    <div key={i}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{kw.text}</span>
                        <span className="text-muted-foreground">{kw.mention_count}</span>
                      </div>
                      <div className="mt-1 h-2 w-full rounded-full bg-muted">
                        <div
                          className={`h-2 rounded-full ${sentimentColor}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="flex h-[200px] items-center justify-center text-sm text-muted-foreground">
                Aucune donnée disponible
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
