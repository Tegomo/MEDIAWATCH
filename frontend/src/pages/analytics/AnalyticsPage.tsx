import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react'
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
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <BarChart3 className="h-6 w-6" />
          Analyses et Tendances
        </h1>
        <p className="text-muted-foreground">
          Visualisez l'évolution des mentions et la répartition par sources
        </p>
      </div>

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
