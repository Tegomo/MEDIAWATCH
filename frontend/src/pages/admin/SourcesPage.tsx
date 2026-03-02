import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, Server, CheckCircle, AlertTriangle, XCircle, Ban, Plus } from 'lucide-react'
import SourceHealthTable from '@/components/admin/SourceHealthTable'
import SourceFormModal from '@/components/admin/SourceFormModal'
import api from '@/services/api'

interface HealthSummary {
  total: number
  enabled: number
  ok: number
  warning: number
  error: number
  disabled: number
}

interface SourcesResponse {
  sources: Array<{
    id: string
    name: string
    url: string
    type: string
    scraper_class: string
    scraping_enabled: boolean
    prestige_score: number
    status: 'ok' | 'warning' | 'error' | 'disabled'
    consecutive_failures: number
    last_scrape_at: string | null
    last_success_at: string | null
    last_error_message: string | null
    articles_24h: number
    total_articles: number
  }>
  summary: HealthSummary
}

interface SourceFormData {
  id?: string
  name: string
  url: string
  type: string
  scraper_class: string
  prestige_score: number
  scraping_enabled: boolean
}

export default function SourcesPage() {
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null)
  const [editingSource, setEditingSource] = useState<SourceFormData | null>(null)

  const { data, isLoading, refetch, isRefetching } = useQuery<SourcesResponse>({
    queryKey: ['admin-sources'],
    queryFn: async () => {
      const resp = await api.get<SourcesResponse>('/admin/sources')
      return resp.data
    },
    refetchInterval: 30 * 1000,
  })

  const summary = data?.summary

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Server className="h-6 w-6" />
            Monitoring Sources
          </h1>
          <p className="text-muted-foreground">
            Statut de santé des sources de scraping
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => { setFormMode('create'); setEditingSource(null) }}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Nouvelle source
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

      {/* Summary cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">OK</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{summary.ok}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Instables</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{summary.warning}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">En erreur</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{summary.error}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Désactivées</CardTitle>
              <Ban className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-500">{summary.disabled}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sources table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : data ? (
        <SourceHealthTable
          sources={data.sources}
          onRefresh={() => refetch()}
          onEdit={(source) => {
            setEditingSource({
              id: source.id,
              name: source.name,
              url: source.url,
              type: source.type,
              scraper_class: source.scraper_class,
              prestige_score: source.prestige_score,
              scraping_enabled: source.scraping_enabled,
            })
            setFormMode('edit')
          }}
          onDelete={async (sourceId, sourceName) => {
            if (!confirm(`Supprimer la source "${sourceName}" et tous ses articles ? Cette action est irréversible.`)) return
            try {
              await api.delete(`/admin/sources/${sourceId}`)
              refetch()
            } catch { /* */ }
          }}
        />
      ) : null}

      {/* Create / Edit modal */}
      {formMode && (
        <SourceFormModal
          mode={formMode}
          initialData={editingSource}
          onClose={() => { setFormMode(null); setEditingSource(null) }}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  )
}
